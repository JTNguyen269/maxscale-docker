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

You can then go into MariaDB to check what databases are present by typing in:
```
mariadb -umaxuser -pmaxpwd -h 127.0.0.1 -P 4000
```
Followed by:
```
show databases;
```

It should look like this:
```
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| zipcodes_one       |
| zipcodes_two       |
+--------------------+
```

**Note: You may encounter some errors when trying to access MariaDB. One of the errors I dealt with was:
`ERROR 1045 (28000): Access denied for user 'maxuser'@'172.21.0.1' (using password: YES)`. With each container created, it typically assigns itself an individual IP that differs from the virtual machine itself.**

To resolve this, I had to go into the shell of each MariaDB container and grant privilages followed by flushing. If you happen to run into this error, here are the steps I performed to debug this issue:

1. Access MariaDB container with:
   ```
   exec -it maxscale_maxscale_1
   ```
2. Then once you are inside the container's shell, type in this command:
   ```
   mysql -umaxuser -pmaxpwd
   ```
3. Next, you'll need to run the `GRANT` command to grant privilages to `maxuser` from IP `172.21.0.1` with this command:
   ```
   GRANT ALL PRIVILEGES ON *.* TO 'maxuser'@'172.21.0.1' IDENTIFIED BY 'maxpwd';
   ```
4. Then you'll need to flush privilages after executing the `GRANT` command to apply these changes:
   ```
   FLUSH PRIVILEGES;
   ```
5. You can now exit out of MariaDB by typing `exit;` and then `exit;` again to exit out of the container's shell.
6. You'll want to repeat these steps for ports `4001 and 4002`which are `maxscale_primary1_1` and `maxscale_primary2_1`.
   
---

## Python Script

Ensure that your containers are up and running on your virtual machine with `sudo docker-compose up -d`
**Note: We will be running the Python Script on the Host machine**

Launch PyCharm IDE on your Host machine and verify the database connection:
```ruby
def connect_to_db():
    con = mysql.connector.connect(
        user='maxuser',
        password='maxpwd',
        host='10.0.0.36',  # Use VM IP
        port='4000'  # Specify port
    )
    return con
```
**Note: You will have to change the following line `host='10.100.10.128',` to your virtual machine's IP address.**
You can do this by typing in `ifconfig` inside the terminal of your virtual machine under `enp0s3`.

Once that is done, proceed by running the script. It should return the following queries:

<details>
<summary>Query 1: Largest zipcode in zipcodes_one</summary>

Largest zipcode in zipcodes_one: 47750

</details>

<details>
<summary>Query 2: List of zipcodes from both databases in Kentucky</summary>

List of Zipcodes from both databases in Kentucky
41503
42201
42202
42120
40801
42602
41601
42204
42020
42603
42122
40402
41121
40902
42021
40903
41712
41512
40803
41101
41102
41105
41114
42206
42123
41602
41713
40003
42022
41603
40906
40946
40004
42023
42024
42402
40104
40806
41714
41311
41203
41604
42320
40006
42322
42323
42324
42207
41513
41514
41535
41567
40807
42025
40403
40404
42516
40007
41605
40913
41606
42712
40914
40405
40808
40915
41804
41832
41124
41160
41226
40810
40816
40008
41607
42027
42713
41719
41314
41351
41364
41204
40107
42101
42102
42103
42104
42128
40009
40108
42715
42741
42325
40409
42518
40109
42210
40921
40410
41721
40010
42716
41722
41517
40310
42717
42028
42519
42211
42327
42371
42029
40813
40011
40075
42718
42719
42733
40376
41301
41360
41519
42720
42721
42722
41408
40923
40311
40350
41725
41128
41129
42127
40815
42724
42214
42328
42330
42215
40012
41727
42726
42404
40312
41317
40313
42332
40110
42216
42031
40927
40111
40819
42728
42753
42032
41729
40701
40702
41731
41819
42406
40013
40419
40820
42033
40014
41413
42217
41810
42333
42729
40823
42035
40115
41615
40422
40423
40452
41616
42408
40824
41812
41735
40316
40930
42036
41736
42409
41520
42321
42326
42337
42731
42219
42338
42339
42528
41621
41739
42037
42410
40729
41622
42732
40018
42038
42129
40117
42701
42702
41522
41542
42220
42280
40317
40019
40730
41740
40826
41815
40827
42567
40828
40843
41425
40118
40020
42221
41426
40932
40119
42039
40319
42040
41524
42533
40022
40023
41743
41219
40935
40997
41139
41526
42343
42361
41527
42223
40121
40122
42133
40939
40940
40601
40602
40603
40604
40618
40619
40620
40621
40622
42134
42135
42411
41528
40322
42041
42140
40140
41817
40941
41630
41632
41141
41745
40324
42044
40943
42131
42141
42142
42156
42740
40025
40944
40026
42232
42742
42344
41142
42045
40328
40734
40434
40829
41143
42743
41144
42345
41631
40142
42234
41222
41821
42047
42413
41746
41747
42048
40143
40171
41531
42746
40818
40831
40840
40858
40144
40178
41635
40330
40027
42347
42348
42364
41701
41702
41723
42049
41332
41333
40949
41534
42419
42420
42236
42050
42051
41636
40951
41822
40953
42152
41132
41146
42748
42153
42240
42241
42349
42749
40844
40145
41640
40845
40437
41749
41762
41766
41214
41224
40955
40336
40472
40146
42350
41338
41824
41149
41642
41825
41307
41310
41339
41366
41390
42629
41751
41774
40337
41537
41563
41826
42252
41538
40440
40737
40339
40847
40958
42053
41539
40442
42054
41828
41859
42154
41754
42055
42056
41643
42254
40031
40032
40444
40446
40342
40033
40150
41831
42058
42754
42755
40849
42256
42351
40502
40503
40504
40505
40506
40507
40508
40509
40510
40511
40512
40513
40514
40515
40516
40517
40522
40523
40524
40526
40533
40536
40544
40546
40550
40555
40574
40575
40576
40577
40578
40579
40580
40581
40582
40583
40588
40591
40598
42539
41540
40740
41834
42352
40445
40460
40724
40741
40742
40743
40744
40745
41347
40037
41348
41201
41230
40201
40202
40203
40204
40205
40206
40207
40208
40209
40210
40211
40212
40213
40214
40215
40216
40217
40218
40219
40220
40221
40222
40223
40224
40225
40228
40229
40231
40232
40233
40241
40242
40243
40245
40250
40251
40252
40253
40255
40256
40257
40258
40259
40261
40266
40268
40269
40270
40272
40280
40281
40282
40283
40285
40287
40289
40290
40291
40292
40293
40294
40295
40296
40297
40298
40299
40129
42060
41231
42061
41232
40854
40855
42063
41543
41544
41558
40152
41647
42354
40447
40488
40448
40153
41835
42355
40040
42431
42757
41547
41836
41451
42259
40962
42436
42758
42064
42759
42631
41159
41649
40830
40964
40041
42066
41837
41838
41855
41234
40334
40346
42069
41612
41650
42541
40965
40347
42070
40348
42762
40045
41651
40856
41352
42633
40351
42437
42261
42440
40046
42157
42764
40353
40456
40473
40047
41839
41548
40155
42765
42071
41549
42544
40048
41840
40049
40050
42076
40051
40052
40355
40340
40356
40357
42442
42262
42159
41238
41164
42265
40358
40972
40981
41459
42301
42302
42303
42304
42334
42356
40359
40360
40366
42001
42002
42003
40461
41216
41240
41257
40361
40362
42160
42634
40464
40862
40863
40157
42266
40055
40363
40468
40056
41553
42366
41554
41501
41502
41571
41250
42635
41843
40977
41555
41844
41861
40755
40036
40057
42444
40058
42367
41845
41645
41653
41362
42445
41619
41655
40059
42441
42450
40865
41166
41557
40159
40160
40060
41847
42451
41559
42638
42368
40161
40475
40476
40162
41254
40979
42452
41560
42273
42274
40759
41561
42369
42163
41365
42370
42275
41367
41848
41464
41168
41169
42642
42276
42372
40370
40061
42453
40062
41368
40063
42078
40371
40372
41465
40481
41171
41759
40982
42553
42164
42455
41849
42079
40983
40374
41562
40065
40066
40165
41564
40763
40067
42456
41763
41764
40068
42081
42457
42171
41173
42501
42502
42503
42564
42776
42374
41174
41175
42458
40069
41256
40379
40484
40380
41659
42647
41566
40170
40868
40988
41568
42649
42459
42460
40070
42124
42130
42166
42782
42285
42082
42558
40071
41660
41260
42083
41189
42084
41262
42151
42167
41862
40870
41663
42286
40995
41263
40486
41264
42461
42784
42376
41135
41179
41385
41265
40383
40384
41772
41760
41773
41386
40175
41572
40385
40076
40873
40874
41267
42085
42462
41666
40489
41180
40176
41667
40387
41775
41421
41472
41477
42377
42086
40177
40077
41268
42463
41669
42788
42464
41833
41858
42378
42653
42087
40492
41181
40769
41271
40078
40390
40391
40392
42565
42088
41255
41274
40771
42170
42288
41776
41183
41777
41778
42566
41397
41001
41002
41003
41004
41005
41006
41007
41008
41045
41010
41011
41012
41014
41015
41016
41017
41018
41019
41030
41031
41033
41034
41035
41037
41039
41040
41041
41022
41042
41043
41044
41046
41048
41049
41051
41052
41053
41054
41055
41056
41059
41061
41062
41063
41064
41065
41071
41072
41073
41074
41075
41076
41099
41080
41081
41083
41085
41086
41091
41092
41093
41094
41095
41096
41097
41098

</details>


---

## Credits
ERROR 1045 (28000) debugging
- [Source 1](https://stackoverflow.com/questions/62617460/mysql-docker-container-error-1045-28000-access-denied-for-user-rootloca)
- [Source 2](https://stackoverflow.com/questions/23950722/how-to-overcome-error-1045-28000-access-denied-for-user-odbclocalhost-u)




