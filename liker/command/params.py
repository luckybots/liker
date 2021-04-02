from tengine import CommandParam

command_params = [
    CommandParam(name='--password',
                 help_str='Password to access the bot admin commands',
                 param_type=str),
    CommandParam(name='--name',
                 help_str='Name of a variable to read',
                 param_type=str),
    CommandParam(name='--value',
                 help_str='Value to set',
                 param_type=str),
]
