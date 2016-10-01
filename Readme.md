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

Or it could be at the following path in the hortonworks distribution.

    /usr/hdp/2.4.2.0-258/hadoop-mapreduce/hadoop-streaming.jar

We suggest to export a variable HS (Hadoop streaming) to use shorter commands

    export HS=/usr/hdp/2.4.2.0-258/hadoop-mapreduce/hadoop-streaming.jar

You can check that the jar works launching it and printing the help.

    hadoop jar $HS --help


Now we can run a map reduce job to count the words in the file we previously uploaded:
```
hadoop jar $HS  \
   -input file.txt \
   -output output_new_0 \
   -mapper mapper.py \
   -reducer reducer.py \
   -file mapper.py \
   -file reducer.py \
   -numReduceTasks 1
```
Please remember the -input and -output files are on the HDFS storage and not in your local disk.
The files passed with the `-file` argument are instead on the local disk, and they are called so that the master node copies these
files on all the slaves nodes automatically.

Also, `output_new_0` is a folder. If the folder already exist on HDFS Hadoop will refuse to start,
because it will not overwrite existing data.

    hdfs dfs -ls
    hdfs dfs -cat output_new_0/part-00000


Now lets make an example that makes more sense, lets count the words of "La Divinia Commedia".
You can find the book the file `dcu.txt`.

You have to upload the file to HDFS as you did for the previous file.

```
hadoop jar $HS  \
   -input dcu.txt \
   -output output_new_0 \
   -mapper mapper.py \
   -reducer reducer.py \
   -file mapper.py \
   -file reducer.py \
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
    <name>fs.swift.impl</name>
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

The Openstack Sahara project provides a more updated version of this jar. We suggest to compile the latest sources if you want a more recent version.
You can compile the jar on any Ubuntu Trusty as follows:

```
git clone https://github.com/openstack/sahara-extra
cd sahara-extra
./tools/build-hadoop-openstack.sh 1 2.7.1
cp  dist/hadoop-openstack/1/hadoop-openstack-2.7.1.jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-openstack-2.7.1.jar
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

    export OS_USERNAME=SWITCHEngines-username
    export OS_PASSWORD=secret
    export OS_TENANT_NAME=SWITCHEngines-tenant
    export OS_AUTH_URL=https://keystone.cloud.switch.ch:5000/v2.0
    export OS_REGION_NAME=LS
    # you can put the export lines in a file called ~/switchengines-rc and later just source it:
    # source ~/switchengines-rc
    swift post mybigdatacontainer

and use Hadoop to copy data into it:

     hadoop distcp dcu.txt swift://mybigdatacontainer.switchengines/dcu.txt

If everything worked you should see the file in SWIFT

     swift list mybigdatacontainer

We are now ready to start the same map reduce job that we did on the HDFS example. We just need to specify that we want to read and write the data from SWIFT:

```
hadoop jar $HS \
-input swift://mybigdatacontainer.switchengines/dcu.txt \
-output swift:///mybigdatacontainer.switchengines/output_new_0 \
-mapper mapper.py \
-reducer reducer.py \
-file mapper.py \
-file reducer.py \
-numReduceTasks 1
```

At the end you should be able to download your result from SWIFT

    swift ls mybigdatacontainer
    swift download mybigdatacontainer output_new_0/part-00000

We conclude with a professional tip ! :) If you dont want to save your password in the file `/etc/hadoop/core-site.xml` in cleartext, you can insert the password in the commandline at every run.
Remeber to put an empty space before the command ( `hadoop` in our case) so that the command will not be saved in your bash history.

```
 hadoop jar $HS \
-D fs.swift.service.switchengines.password=mysecretsecretpassword \
-input swift://mybigdatacontainer.switchengines/dcu.txt \
-output swift:///mybigdatacontainer.switchengines/output_new_0 \
-mapper mapper.py \
-reducer reducer.py \
-file mapper.py \
-file reducer.py \
-numReduceTasks 1
```

In general with this `-D` flag you can override any configuration from the `/etc/hadoop/core-site.xml`

## Use Openstack SWIFT to access a public dataset on SWITCHengines

To get started with Public Datasets hosted on SWITCHengines we loaded the googlebooks-ngrams dataset: http://storage.googleapis.com/books/ngrams/books/datasetsv2.html
The dataset is about 5Tb of zipped files.

To write this part of the tutorial I read first this blog post:
https://dbaumgartel.wordpress.com/2014/04/10/an-elastic-mapreduce-streaming-example-with-python-and-ngrams-on-aws/

We are going to so something similar but using Openstack instead of Amazon EC2.

We will analyze a part of the dataset to understand how many words that start with the letter X appeared for the first time in the year 1999.
Check the code in the files `mapper-ngrams.py` and `reducer-ngrams.py`.

To configure Hadoop to access the dataset, add a new block in the `core-site.xml` config file.
```
<property>
   <name>fs.swift.service.datasets.auth.url</name>
   <value>https://keystone.cloud.switch.ch:5000/v2.0/tokens</value>
 </property>
 <property>
   <name>fs.swift.service.datasets.auth.endpoint.prefix</name>
   <value>/AUTH_</value>
 </property>
 <property>
   <name>fs.swift.service.datasets.http.port</name>
   <value>443</value>
 </property>

 <property>
   <name>fs.swift.service.datasets.region</name>
   <value>LS</value>
 </property>
 <property>
   <name>fs.swift.service.datasets.public</name>
   <value>true</value>
 </property>
 <property>
   <name>fs.swift.service.datasets.tenant</name>
   <value>datasets_readonly</value>
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

*Make sure SWITCHengines admins added your user to the tenant datasets_readonly before trying the next steps. Contact support if unsure about this.*

Now we should be able to download this file:

    export OS_USERNAME=SWITCHengines-username
    export OS_PASSWORD=secret
    export OS_TENANT_NAME=datasets_readonly
    export OS_AUTH_URL=https://keystone.cloud.switch.ch:5000/v2.0
    export OS_REGION_NAME=LS
    swift download  googlebooks-ngrams-gz-swift eng/googlebooks-eng-all-1gram-20120701-x.gz

Let's check if our data pipeline works before using Hadoop for this map reduce example.

    time zcat googlebooks-eng-all-1gram-20120701-x.gz | ./mapper-ngrams.py | sort -k1,1 | ./reducer-ngrams.py | sort -k2,2n

The result should be a set with the words that appeared for the first time in the year 1999 and that start with the letter X and the number of occurences.

Because we limited our analisys to a single file of 14Mb we are still able to check the pipeline without using Hadoop.

Now we will do the same using Hadoop, reading the single file `googlebooks-eng-all-1gram-20120701-x.gz` from the swift container with the googlebooks-ngrams dataset and writing the result in swift in a container in our own tenant.
Note that Hadoop is able to understand automatically that the input file is in zip format, and it will decompress it without any special configuration.

```
hadoop jar /usr/lib/hadoop/hadoop-2.7.1/share/hadoop/tools/lib/hadoop-streaming-2.7.1.jar \
-D fs.swift.service.switchengines.password=mysecretsecretpassword \
-input swift://googlebooks-ngrams-gz-swift.datasets/eng/googlebooks-eng-all-1gram-20120701-x.gz \
-output swift://results.switchengines/testnumber1 \
-mapper mapper-ngrams.py \
-reducer reducer-ngrams.py  \
-file mapper-ngrams.py \
-file reducer-ngrams.py  \
-numReduceTasks 1
```

When Hadoop finishes the processing you can download the results:

    swift download results testnumber1/part-00000

The result should be the same as the one you observed when testing the data pipeline.

Now lets try with the file eng/googlebooks-eng-all-1gram-20120701-a.gz that is about 300Mb

```
hadoop jar $HS \
-D fs.swift.service.switchengines.password=mysecretsecretpassword \
-D fs.swift.service.datasets.password=mysecretsecretpassword \
-file mapper-ngrams.py \
-file reducer-ngrams.py \
-input swift://googlebooks-ngrams-gz-swift.datasets/eng/googlebooks-eng-all-1gram-20120701-a.gz \
-output swift://results.switchengines/testnumber2 \
-mapper mapper-ngrams.py \
-reducer reducer-ngrams.py  \
-numReduceTasks 1
```

When the processing is finished you will be able to download the output from swift

    swift download results testnumber2/part-00000

## Use S3 to access a public dataset on SWITCHengines

SWITCHengines also provides a object storage with S3 api. Usually the `s3a` driver is already installed in Hadoop, you will not need to add a jar file for this setup.

Because the config parameters are many, we suggest to leave alone the `core-site.xml` global file. Create a file named `s3.xml` , pay attention to the first three properties that you will most likely want to change. The rest should be cut and paste. Make sure you are familiar with this reference documentation: https://help.switch.ch/engines/documentation/s3-like-object-storage/

Here is the `s3.xml` content:

```
<configuration>
<property>
  <name>fs.s3a.access.key</name>
  <description>AWS access key ID. Omit for Role-based authentication.</description>
  <value>Your_secret_value</value>
</property>

<property>
  <name>fs.s3a.secret.key</name>
  <description>AWS secret key. Omit for Role-based authentication.</description>
  <value>Your_secret_value</value>
</property>

<property>
  <name>fs.s3a.endpoint</name>
  <description>AWS S3 endpoint to connect to. An up-to-date list is
    provided in the AWS Documentation: regions and endpoints. Without this
    property, the standard region (s3.amazonaws.com) is assumed.
    For SWITCHengines possible values are os.unil.cloud.switch.ch
    or os.zhdk.cloud.switch.ch
  </description>
  <value>os.unil.cloud.switch.ch</value>
</property>

<property>
  <name>fs.s3a.connection.maximum</name>
  <value>15</value>
  <description>Controls the maximum number of simultaneous connections to S3.</description>
</property>

<property>
  <name>fs.s3a.connection.ssl.enabled</name>
  <value>true</value>
  <description>Enables or disables SSL connections to S3.</description>
</property>


<property>
  <name>fs.s3a.attempts.maximum</name>
  <value>10</value>
  <description>How many times we should retry commands on transient errors.</description>
</property>

<property>
  <name>fs.s3a.connection.establish.timeout</name>
  <value>5000</value>
  <description>Socket connection setup timeout in milliseconds.</description>
</property>

<property>
  <name>fs.s3a.connection.timeout</name>
  <value>50000</value>
  <description>Socket connection timeout in milliseconds.</description>
</property>

<property>
  <name>fs.s3a.paging.maximum</name>
  <value>5000</value>
  <description>How many keys to request from S3 when doing
     directory listings at a time.</description>
</property>

<property>
  <name>fs.s3a.threads.max</name>
  <value>256</value>
  <description> Maximum number of concurrent active (part)uploads,
  which each use a thread from the threadpool.</description>
</property>
<property>
  <name>fs.s3a.threads.core</name>
  <value>15</value>
  <description>Number of core threads in the threadpool.</description>
</property>

<property>
  <name>fs.s3a.threads.keepalivetime</name>
  <value>60</value>
  <description>Number of seconds a thread can be idle before being
    terminated.</description>
</property>
<property>
  <name>fs.s3a.max.total.tasks</name>
  <value>1000</value>
  <description>Number of (part)uploads allowed to the queue before
  blocking additional uploads.</description>
</property>

<property>
  <name>fs.s3a.multipart.size</name>
  <value>104857600</value>
  <description>How big (in bytes) to split upload or copy operations up into.</description>
</property>

<property>
  <name>fs.s3a.multipart.threshold</name>
  <value>2147483647</value>
  <description>Threshold before uploads or copies use parallel multipart operations.</description>
</property>

<property>
  <name>fs.s3a.acl.default</name>
  <description>Set a canned ACL for newly created and copied objects. Value may be private,
     public-read, public-read-write, authenticated-read, log-delivery-write,
     bucket-owner-read, or bucket-owner-full-control.</description>
</property>

<property>
  <name>fs.s3a.multipart.purge</name>
  <value>false</value>
  <description>True if you want to purge existing multipart uploads that may not have been
     completed/aborted correctly</description>
</property>

<property>
  <name>fs.s3a.multipart.purge.age</name>
  <value>86400</value>
  <description>Minimum age in seconds of multipart uploads to purge</description>
</property>

<property>
  <name>fs.s3a.buffer.dir</name>
  <value>${hadoop.tmp.dir}/s3a</value>
  <description>Comma separated list of directories that will be used to buffer file
    uploads to. No effect if fs.s3a.fast.upload is true.</description>
</property>

<property>
  <name>fs.s3a.impl</name>
  <value>org.apache.hadoop.fs.s3a.S3AFileSystem</value>
  <description>The implementation class of the S3A Filesystem</description>
</property>
</configuration>
```

Now lets make a new example where we read the data from S3, and we store the result in HDFS.

We can use the `-conf` flag, to read the S3 configuration from the external file. This would be the final command:

```
hadoop jar $HS \
-conf ~/s3.xml \
-file mapper-ngrams.py \
-file reducer-ngrams.py \
-input s3a://googlebooks-ngrams-gz/eng/googlebooks-eng-all-1gram-20120701-a.gz \
-output myhdfsfolder \
-mapper mapper-ngrams.py \
-reducer reducer-ngrams.py  \
-numReduceTasks 1
```

## Final troubleshooting notes

If you need to debug you can enable the Hadoop debug setting the `HADOOP_ROOT_LOGGER` variable in this way:

    HADOOP_ROOT_LOGGER=DEBUG,console hadoop fs -ls swift://googlebooks-ngrams-gz-swift.datasets/

If you are doing some tests with your own swift installation, using a self signed SSL certificate, this command explains how to alter the Java keystgore used by Hadoop

    keytool -import -noprompt -trustcacerts -alias garr -file /home/ubuntu/DigiCertCA.crt -keystore /usr/lib/java/jdk1.8.0_74/jre/lib/security/cacerts`

with default password `changeit` for the Java Key Store
