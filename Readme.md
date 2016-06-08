# Hadoop tutorial for SWITCHengines

This is a tutorial for Hadoop beginners.

We assume that your cluster is already installed on top of SWITCHengines, and you can ssh to the master node of the cluster.

## Your first map reduce


First we run a functional test to check that we can run a map reduce job. The goal is to count how many times a word appears in a string.

Let's create a file with an example string:

    echo "A long long time ago I read the Hadoop book, but this book was so long I forgot most of it" > file.txt

Now we need to upload `file.txt` to the HDFS storage. (It should be the default storage)

    hdfs dfs -put file.txt

You can check if the file is correctly uploaded:

    hdfs dfs -ls

For this test we will use the streaming API of Hadoop that makes possible to write the map and reduce function in any language. We provide for this example the `mapper.py` and `reducer.py` files.

You can check that the data processing pipeline works without Hadoop using standard UNIX pipes:

    cat file.txt | ./mapper.py

This will print the output after the mapping, to check also the final output after the reducing:

    cat file.txt | ./mapper.py | sort | ./reducer.py

Lets know test this with Hadoop.

Identify where is in your system the `hadoop-straming-<version>.jar` file. In our case it is at

    /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar

You can check that the jar works launching it and printing the help.

    hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar --help


Now we can run a map reduce job to count the words in the file we previously uploaded:
```
hadoop jar hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar  \
   -input file.txt \
   -output output_new_0 \
   -mapper mapper.py \
   -reducer reducer.py \
   -numReduceTasks 1
```
Please remember the -input and -output files are on the HDFS storage and not in your local disk.

Also, `output_new_0` is a folder. If the folder already exist on HDFS Hadoop will refuse to start,
because it will not overwrite existing data.

    hdfs dfs -ls
    hdfs dfs -cat output_new_0/part-00000


Now lets make an example that makes more sense, lets count the words of "La Divinia Commedia".
You can find the book the file `dcu.txt`.

You have to upload the file to HDFS as you did for the previous file.

```
hadoop jar hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar  \
   -input dcu.txt \
   -output output_new_0 \
   -mapper mapper.py \
   -reducer reducer.py \
   -numReduceTasks 1
```

## Use Openstack SWIFT block storage instead of HDFS

If your Hadoop cluster runs on top SWITCHengines Openstack, you might prefer to use SWIFT object storage instead
of HDFS on top of Cinder volumes. Cinder volumes could be implemented on top of Ceph RBD that already makes 3 times replicas at the block level, and this makes not very convenient to run HDFS with maybe an additional replica factor of 3 or 5 on top of it. Moreover HDFS design implies data locality. If the cinder volumes of your Virtual Machines are not local, it makes really no sense to run HDFS on top of them.

### Check if your Hadoop installation supports SWIFT

To write this tutorial I read this references:
 - http://docs.openstack.org/developer/sahara/userdoc/hadoop-swift.html
 - http://spark.apache.org/docs/latest/storage-openstack-swift.html

Check this configuration file:

    /etc/hadoop/core-site.xml

You should check the all the information to connect to swift are present.

```
<property>
    <name>fs.swift.impl</name
 <value>org.apache.hadoop.fs.swift.snative.SwiftNativeFileSystem</value>
</property>

 <property>
    <name>fs.swift.service.switchengines.auth.url</name>
    <value>https://keystone.cloud.switch.ch:5000/v2.0/tokens</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.auth.endpoint.prefix</name>
    <value>/AUTH_</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.http.port</name>
    <value>443</value>
  </property>

  <property>
    <name>fs.swift.service.switchengines.region</name>
    <value>LS</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.public</name>
    <value>true</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.tenant</name>
    <value>SWITCHengines-tenant-name</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.username</name>
    <value>SWITCHengines-username</value>
  </property>
  <property>
    <name>fs.swift.service.switchengines.password</name>
    <value>secret</value>
  </property>
```

Your Hadoop distribution already contains a jar with the `org.apache.hadoop.fs.swift.snative.SwiftNativeFileSystem` class. You should find it at this location:

    /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-openstack-2.7.1.jar

The Openstack Sahara project provides a more updated version of this jar. To update just overwrite the file.
```
wget http://sahara-files.mirantis.com/hadoop-swift/hadoop-openstack-latest.jar
cp hadoop-openstack-latest.jar     /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-openstack-2.7.1.jar
```

You should make sure this jar file is in your classpath, otherwise you will get the `java.lang.RuntimeException: java.lang.ClassNotFoundException: Class org.apache.hadoop.fs.swift.snative.SwiftNativeFileSystem not found`

To check the current classpath you can run:

```
hadoop classpath
```

Usually you have a empty `HADOOP_CLASSPATH` env variable. Use it to modify the classpath:

```
export HADOOP_CLASSPATH=/usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/*
hadoop classpath
```


Let's now create a container:

    source ~/switchengines-rc
    swift post mybigdatacontainer

and use Hadoop to copy data into it:

     hadoop distcp dcu.txt swift://mybigdatacontainer.switchengines/dcu.txt

If everything worked you should see the file in SWIFT

     swift ls mybigdatacontainer

We are now ready to start the same map reduce job that we did on the HDFS example. We just need to specify that we want to read and write the data from SWIFT:

```
hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar \
-input swift://mybigdatacontainer.switchengines/dcu.txt \
-output swift:///mybigdatacontainer.switchengines/output_new_0 \
-mapper mapper.py \
-reducer reducer.py \
-numReduceTasks 1
```

At the end you should be able to download your result from SWIFT

    swift ls mybigdatacontainer
    swift download mybigdatacontainer output_new_0/part-00000

We conclude with a professional tip ! :) If you dont want to save your password in the file `/etc/hadoop/core-site.xml` in cleartext, you can insert the password in the commandline at every run.
Remeber to put an empty space before the command ( `hadoop` in our case) so that the command will not be saved in your bash history.

```
 hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar \
-D fs.swift.service.switchengines.password=mysecretsecretpassword \
-input swift://mybigdatacontainer.switchengines/dcu.txt \
-output swift:///mybigdatacontainer.switchengines/output_new_0 \
-mapper mapper.py \
-reducer reducer.py \
-numReduceTasks 1
```

In general with this `-D` flag you can override any configuration from the `/etc/hadoop/core-site.xml`
