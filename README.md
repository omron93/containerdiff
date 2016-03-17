# ContainerDiffTool

Tool to show changes among two container images.

### Usage
```
usage: containerdiff [-h] [-o OUTPUT] [-s] [-f [FILTER]] [-l {10,20,30,40,50}]
                     [-d] [--version]
                     imageID imageID
```

| Positional arguments | Description                                         |
| -------------------- | --------------------------------------------------- |
|  imageID             | ID of container image from/to which to show changes |

| Optional arguments         | Description                                                     |
| -------------------------- | ----------------------------------------------------------------|
| -h, --help                 | Show this help message and exit                                 |
| -o OUTPUT, --output OUTPUT | Output file.                                                    |
| -s, --silent               | Lower verbosity of diff output. See help of individual tests.   |
| -f [FILTER], --filter [FILTER] | Enable filtering. Specify JSON file with options ("./filter.json" by default). |
| -l {10,20,30,40,50}, --logging {10,20,30,40,50} | Print additional logging information.      |
| -d, --debug                | Print additional debug information (= -l 10).                   |
| --version                  | Show program's version number and exit                          |
