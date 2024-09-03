# dev_utils
Tools I commonly use in my Deep Learning projects.

# Installation

Requirement: python>=3.8 

Quick install:
```bash
pip install git+https://github.com/NSavov/dev_utils.git
```

Or install from the project directory after cloning:
```bash
pip install -e .
```

# Tools

## Logger

This is a descriptive logger with messages containing a timestamp, class name and a tag, with colorization and customization support.

We define a `Logger` class and a `getLogger()` method to replace the standard one. 
Inside the `Logger`, together with the already available `debug()`, `error()`, `warning()` and `info()` we define their customized versions with colorized text and an arbitrary number of arguments to log (in the style of `print()`): `d()`, `e()`, `w()` and `i()`. In addition, we define `t()` (standing for test), that is another info level log method with the goal of a debug prints that does not require activating debug log level (which often results in redundant logs from external libraries), but still is easily distinguishable from info messages in log appearance and in the source code.

For each logger that we define we decide on a name tag. THe logger will identify itself in the log with this name. Basic example usage:
```python
import dev_utils.logger as dl
import logging    
logging.basicConfig(level=logging.INFO)
log = dl.getLogger("test")

# Example usage
class MyClass:
    def my_method(self):
        log.i("This is an info message")


my_instance = MyClass()
my_instance.my_method()
```

If unspecified, a random color will be selected for the tags. To customize the color, use:
```python
log = getLogger("test", name_color="GREEN", class_colors="BRIGHT_WHITE")
```

* `name_color` - determines the color of the name of the logger (the chosen tag)
* `class_colors` - determines the class color(s). It can be a single color to be used with all classes or a dictionary with class name keys and corresponding color strings.

The colors can be one of the following ANSI colors (described with a string):
```
BLACK
RED
GREEN
YELLOW
BLUE
MAGENTA
CYAN
WHITE
BRIGHT_BLACK
BRIGHT_RED
BRIGHT_GREEN
BRIGHT_YELLOW
BRIGHT_BLUE
BRIGHT_MAGENTA
BRIGHT_CYAN
BRIGHT_WHITE
ORANGE
BRIGHT_ORANGE
PURPLE
BRIGHT_PURPLE
BROWN
PINK
BRIGHT_PINK
```

It is also possible to set an external file for all the loggers to save their logs in, in addition to showing them on the standard output.
```python
import dev_utils.logger as dl
log = dl.getLogger("test")
dl.update_logger_file("./log.txt")
```

## Model Manager

A set of classes to organize checkpoints while training.
Each model saves its checkpoints in a checkpoint directory, located in a root directory path. All model direcotries are expected to be saved there. Each directory has the name format `{MODEL_ID}_{DESCRIPTION}`, where `MODEL_NAME` is a model number identifier field with width 3. The ids are seuquentially taken by each new model, model description describes succintly the run and the model and is defined by the user. The `CheckpointsDirManager` class is responsible of managing the direcotries. It has methods for finding models by id, description, last model in line, deleting empty checkpoint directories, creating a new checkpoint directory structure, basic stats. Method names are self explanatory.

Each checkpoint directory contains checkpoint files. `CheckpointManager` class is responsible for managing those files, similarly to `CheckpointDirManager`. Each checkpoint is assigned an id and utility methods for getting the latest one, search by id, etc, are provided.
