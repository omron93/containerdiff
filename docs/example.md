# Containerdiff

Tool to show changes among two container images.

### Example usage

We want to compare two docker images. For this example lets choose CentOS docker images. So we have two images:

[docker.io/centos:7.1.1503](https://hub.docker.com/r/library/centos/) ,
[docker.io/centos:7.2.1511](https://hub.docker.com/r/library/centos/)

and we want to know what is different in 7.2 according to 7.1 image.


Containerdiff tool now supports these tests:
* changes in installed RPM packages
* changes in files not installed by RPM
* changes in container image metadata
* changes in container image history

First we have to pull images.

```
$ docker pull docker.io/centos:7.1.1503
$ docker pull docker.io/centos:7.2.1511
```

Then we can run containerdiff.

```
$ ./containerdiff docker.io/centos:7.1.1503 docker.io/centos:7.2.1511 -o ./result.json -f
```

This command examines changes from first to second specified image, filter them and saves output to file './result.json'.

### Working with containerdiff output

The output of containerdiff is JSON document. To its examining lets use python3.

First run python3 interpreter, import json module and load the result into python.

```python
$ python3
>>> import json
>>> file = open("./result.json")
>>> result = json.load(file)
```

Now variable 'result' contains dictionary. Its keys should correspond to what containerdiff tests. Current implemented tests create these keys:

```python
>>> result.keys()
dict_keys(['history', 'metadata', 'files', 'packages'])
```

To get an explanation for each test you can see [Explanation of a format of test results](./result-explanation.md) and python docstrings. For example to get the documentation of history test run:

```python
>>> import tests.history
>>> help(tests.history)
Help on module tests.history in tests:

NAME
    tests.history - Show diff in container image history.

FUNCTIONS
    dockerfile_from_image(ID, cli)
        Return list of commands used to create image *ID*. These
        commands are get from docker history.
    
    run(image1, image2, silent)
        Test history of the image.
        
        Adds one key to the output of the diff tool:
        "history" - unified_diff style changes in commands used to create
                    the image

DATA
    logger = <logging.Logger object>

FILE
    /home/mas/ContainerDiffTool/tests/history.py
```

### Filtering

Containerdiff also offers ability to filter the output. This is a default 'filter.json' used for filtering in this example. You can specify a custom file with filtering options in '--filter' option. 

```json
{
    "files" : {
        "keys" : ["added", "removed", "modified"],
        "action" : "exclude",
        "data" : ["/var/lib/yum/yumdb",
                  "/var/lib/yum/history",
                  "/var/log/yum.log"]
    },
    "metadata" : {
        "action" : "exclude",
        "data" : ["Size",
                  "DockerVersion",
                  "Id",
                  "GraphDriver",
                  "Created",
                  "RepoTags",
                  "Parent",
                  "ContainerConfig",
                  "RepoDigests'",
                  "Container",
                  "Config:Labels:io.openshift.builder-version"]
    }
}
```

For each test you want to filter there have to be name/value pair in JSON object. Name specifies a name of name/value pair to filter in the result. The value have to be an object with these name/value pairs.

| Name/value pair      | Description                                         |
| -------------------- | --------------------------------------------------- |
| "keys" : [String]    |   Optional. Applicable to tests which result is a dict - this value specifies for which keys to apply filtering. |
| "action" : "include" or "exclude"   |   Mandatory. "include" specifies that only parts of result which match "data" stays in the result. "exclude" specifies that parts of result which match "data" will be removed from result. |
| "data" : [String]    |   Mandatory. Strings are regular expressions. |

