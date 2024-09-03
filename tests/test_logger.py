import logging    
logging.basicConfig(level=logging.DEBUG)

def test_logger():
    from dev_utils.logger import getLogger
    # Logger setup
    logger = getLogger("open-genie", class_colors="BRIGHT_WHITE")

    # Example usage
    class MyClass:
        def my_method(self):
            logger.info("This is an info message")

    # Example usage
    class MyClass2:
        def my_method(self):
            logger.info("This is an info message")

    my_instance = MyClass()
    my_instance.my_method()

    my_instance = MyClass2()
    my_instance.my_method()