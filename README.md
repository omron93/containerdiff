# ContainerDiffTool

Tool to show changes among two container images.

### Usage
```
usage: containerdiff [-h] [-s] [-f [FILTER]] [-o OUTPUT] [-p [DIRECTORY]]
                     [--host HOST] [-l {10,20,30,40,50}] [-d] [--version]
                     imageID imageID
```

| Positional arguments | Description                                         |
| -------------------- | --------------------------------------------------- |
|  imageID             | ID of container image from/to which to show changes |

| Optional arguments         | Description                                                     |
| -------------------------- | ----------------------------------------------------------------|
| -h, --help                 | Show this help message and exit                                 |
| -s, --silent               | Lower verbosity of diff output. See help of individual modules. |
| -f [FILTER], --filter [FILTER] | Enable filtering. Optionally specify JSON file with options (preinstalled "filter.json" by default). |
| -o OUTPUT, --output OUTPUT | Output file.                                                    |
| -p [DIRECTORY], --preserve [DIRECTORY] | Do not remove directories with extracted images. Optionally specify directory where to extact images ("/tmp" by default). |
| --host HOST                | Docker daemon socket to connect to                              |
| -l {10,20,30,40,50}, --logging {10,20,30,40,50} | Print additional logging information.      |
| -d, --debug                | Print additional debug information (= -l 10).                   |
| --version                  | Show program's version number and exit                          |

See [example usage](./docs/example.md).
