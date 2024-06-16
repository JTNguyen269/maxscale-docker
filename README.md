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

## Setup and Configuration

The first thing we'll want to do is clone the [MaxScale repository](https://github.com/JTNguyen269/maxscale-docker).

Open up the terminal inside your virtual machine and type in this following command: `git clone https://github.com/JTNguyen269/maxscale-docker`
If you do not have Git installed, perform the following commands below:
`sudo apt update` to update all packages, followed by `sudo apt install git` to install Git. Verify Git is installed using this command `git --version`



After MaxScale and the servers have started (takes a few minutes), you can find
the readwritesplit router on port 4006 and the readconnroute on port 4008. The
user `maxuser` with the password `maxpwd` can be used to test the cluster.
Assuming the mariadb client is installed on the host machine:
```
$ mysql -umaxuser -pmaxpwd -h 127.0.0.1 -P 4006 test
Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MySQL connection id is 5
Server version: 10.2.12 2.2.9-maxscale mariadb.org binary distribution

Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MySQL [test]>
```
You can edit the [`maxscale.cnf.d/example.cnf`](./maxscale.cnf.d/example.cnf)
file and recreate the MaxScale container to change the configuration.

To stop the containers, execute the following command. Optionally, use the -v
flag to also remove the volumes.

To run maxctrl in the container to see the status of the cluster:
```
$ docker-compose exec maxscale maxctrl list servers
┌─────────┬─────────┬──────┬─────────────┬─────────────────┬──────────┐
│ Server  │ Address │ Port │ Connections │ State           │ GTID     │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼──────────┤
│ server1 │ master  │ 3306 │ 0           │ Master, Running │ 0-3000-5 │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼──────────┤
│ server2 │ slave1  │ 3306 │ 0           │ Slave, Running  │ 0-3000-5 │
├─────────┼─────────┼──────┼─────────────┼─────────────────┼──────────┤
│ server3 │ slave2  │ 3306 │ 0           │ Running         │ 0-3000-5 │
└─────────┴─────────┴──────┴─────────────┴─────────────────┴──────────┘

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
