# MaxScale Docker CNE370

---

## Introduction
This project demonstrates the use of a sharded database architecture, where data is divided across multiple database instances. This approach, known as "sharding," greatly improves performance, scalability, and manageability.

This guide will cover the following below:
- Editing the docker-compose.yml file
  - Maxscale Instance
  - Primary1 table
  - Primary2 table

- Configuring maxscale.cnf file
  - CNF modified to sharding format
  - CNF communicates with 2 primary database shards
 
- Using provided Python script to talk to Maxscale instance and perform database queries
  - Prints largest zipcode within one database
  - Prints zipcodes of specified state from both databases
  - Prints all zipcodes between stated values from both databases
  - Prints TotalWages column of specified state

---

## Prerequisites For Running

We will be using Ubuntu on VirtualBox in this guide. If you are unfamiliar or do not have it installed, you can do so [here](https://www.wikihow.com/Install-Ubuntu-on-VirtualBox).

[Docker](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04) and [Docker-compose](https://docs.docker.com/compose/install/standalone/) must be installed as well.

Python 3 will also need to be installed, which can be found [here](https://www.python.org/downloads/).

The Python IDE used in this guide is [PyCharm Community Edition Version 2023.3.4](https://www.jetbrains.com/pycharm/download/other.html)
- You will need to install the following Python library in order to run the Python script correctly: `mysql-connector`

Also, if you are using an exisiting virtual machine, please ensure that your virtual machine has enough space to perform this project. You can check space availability by typing in this following command in the terminal: `df`. You can use `docker ps -a` or `docker images -a` to check if there are any present containers that are dangling or not being used. A few ways to clear and remove existing docker containers is with `docker rm`, `docker rmi`, `docker system prune -a` or `docker images purge`. There are more ways to go about this but these are just a few commands that may help you free up some space.

---

## Configuration

The first thing we'll want to do is clone the [MaxScale repository](https://github.com/JTNguyen269/maxscale-docker).

Open up the terminal inside your virtual machine and type in this following command:
```
git clone https://github.com/JTNguyen269/maxscale-docker
```

If you do not have Git installed, perform the following commands:
`sudo apt update` to update all packages, followed by `sudo apt install git` to install Git. Verify Git is installed using this command `git --version`

Next step is to go into the maxscale folder. You can do so by typing in this following command:
```
cd maxscale-docker/maxscale
```
This is the folder that we want to be in when we up and run our maxscale and server containers. But first, we will need to configure a few files.

Go into the `maxscale.cnf.d` folder by typing in
```
cd maxscale-docker/maxscale/maxscale.cnf.d
```
And type in `sudo nano example.cnf` to go in and edit the CNF file. You will only be editing the top section of this file. It should look something like this:
```ruby
[server1]
type=server
address=primary1
port=3306
protocol=MariaDBBackend

[server2]
type=server
address=primary2
port=3306
protocol=MariaDBBackend

[Sharded-Service]
type=service
router=schemarouter
servers=server1,server2
user=maxuser
password=maxpwd

[Sharded-Service-Listener]
type=listener
service=Sharded-Service
protocol=MariaDBClient
port=4000
```

We are setting `server1` as `primary1` while `server2` being `primary2`. Also the router used in this guide is the `schemarouter` and we will as be using port 4000 for the listener.
Once you have made those changes, exit out of the file by `Ctrl+X` followed by `Y` to apply changes and then press `Enter`. 

Next, we'll need to configure the yml file. Go back into the maxscale folder by doing `cd ..` and then `sudo nano docker-compose.yml'
Edit the file so it looks like this:

```ruby
version: '2'
services:
    primary1:
        image: mariadb:10.3
        environment:
            MYSQL_ALLOW_EMPTY_PASSWORD: 'Y'
        volumes:
            - ./sql/primary1:/docker-entrypoint-initdb.d
        command: mysqld --log-bin=mariadb-bin --binlog-format=ROW --server-id=3000
        ports:
            - "4001:3306"

    primary2:
        image: mariadb:10.3
        environment:
            MYSQL_ALLOW_EMPTY_PASSWORD: 'Y'
        volumes:
            - ./sql/primary2:/docker-entrypoint-initdb.d
        command: mysqld --log-bin=mariadb-bin --binlog-format=ROW --server-id=3001 
        ports:
            - "4002:3306"

    maxscale:
        image: mariadb/maxscale:latest
        depends_on:
            - primary1
            - primary2
        volumes:
            - ./maxscale.cnf.d:/etc/maxscale.cnf.d
        ports:
            - "4000:4000"  # Shard-Listener
            - "4006:4006"  # readwrite port
            - "4008:4008"  # readonly port
            - "8989:8989"  # REST API port
```
Originally, this file was set up to be a master-slave architecture but is now configured to be a Sharded architecture. An additonal port has been added towards the bottom for `Shard-Listener`. 

---

## Maxscale Docker-Compose Setup

Now with everything configured, we will want to run the following commands:
```
sudo docker-compose build
sudo docker-compose up -d
```
If successful, you should see the terminal returning this message:
`
Starting maxscale_primary2_1 ... done
Starting maxscale_primary1_1 ... done
Starting maxscale_maxscale_1 ... done
`
You can also verify if the containers are up and running by typing in:
```
docker-compose ps
```

To view the layout of your servers, you can type in this following command:
```
docker-compose exec maxscale maxctrl list servers
```

It should return a table like this:
```
┌─────────┬──────────┬──────┬─────────────┬─────────────────┬──────────┬─────────────────────┐
│ Server  │ Address  │ Port │ Connections │ State           │ GTID     │ Monitor             │
├─────────┼──────────┼──────┼─────────────┼─────────────────┼──────────┼─────────────────────┤
│ server1 │ primary1 │ 3306 │ 0           │ Master, Running │ 0-3000-5 │ MariaDB-Monitor     │
├─────────┼──────────┼──────┼─────────────┼─────────────────┼──────────┼─────────────────────┤
│ server2 │ primary2 │ 3306 │ 0           │ Running         │ 0-3000-5 │ MariaDB-Monitor     │
└─────────┴──────────┴──────┴─────────────┴─────────────────┴──────────┴─────────────────────┘
```





The cluster is configured to utilize automatic failover. To illustrate this you can stop the master
container and watch for maxscale to failover to one of the original slaves and then show it rejoining
after recovery:
```
$ docker-compose stop master
Stopping maxscaledocker_master_1 ... done
$ docker-compose exec maxscale maxctrl list servers
┌─────────┬─────────┬──────┬─────────────┬─────────────────┬─────────────┐
│ Server  │ Address │ Port │ Connections │ State           │ GTID        │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server1 │ master  │ 3306 │ 0           │ Down            │ 0-3000-5    │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server2 │ slave1  │ 3306 │ 0           │ Master, Running │ 0-3001-7127 │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server3 │ slave2  │ 3306 │ 0           │ Slave, Running  │ 0-3001-7127 │
└─────────┴─────────┴──────┴─────────────┴─────────────────┴─────────────┘
$ docker-compose start master
Starting master ... done
$ docker-compose exec maxscale maxctrl list servers
┌─────────┬─────────┬──────┬─────────────┬─────────────────┬─────────────┐
│ Server  │ Address │ Port │ Connections │ State           │ GTID        │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server1 │ master  │ 3306 │ 0           │ Slave, Running  │ 0-3001-7127 │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server2 │ slave1  │ 3306 │ 0           │ Master, Running │ 0-3001-7127 │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼─────────────┤
│ server3 │ slave2  │ 3306 │ 0           │ Slave, Running  │ 0-3001-7127 │
└─────────┴─────────┴──────┴─────────────┴─────────────────┴─────────────┘

```

Once complete, to remove the cluster and maxscale containers:

```
docker-compose down -v
```
