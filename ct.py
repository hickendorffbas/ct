#!/usr/bin/python3

import json
import os
import sys



CONF_DIRECTORY = os.getenv("CT_CONF_DIRECTORY")
if CONF_DIRECTORY is None:
    print("ERROR: environment variable CT_CONF_DIRECTORY not set")
    exit()


def load_commands():
    all_commands = {}
    commands_by_context = {}

    for file_name in os.listdir(CONF_DIRECTORY):
        f = open(CONF_DIRECTORY + os.sep + file_name)
        commands_in_file = json.load(f)
        context = file_name.partition(".")[0] 

        commands_by_context[context] = {}

        for key, command in commands_in_file.items():
            if key in all_commands:
                print(f"WARNING: duplicate command definition for \"{key}\" in {file_name}")
            all_commands[key] = command
            commands_by_context[context][key] = command

    return all_commands, commands_by_context



def handle_ct_command(arguments, all_commands, commands_by_context):
    if len(arguments) == 1 and arguments[0] == "list":

        #TODO: add builtin commands to the list (before alphabetic sorting of custom commands)

        #TODO: format nicely
        for key in sorted(all_commands):
            value = all_commands[key]
            print(key, ":", value.get("description", value["command"]))

        return

    if len(arguments) in (3, 4) and arguments[0] == "add":
        new_command_name = arguments[1]
        command_code = arguments[2]
        if len(arguments) == 4:
            context = arguments[3]
        else:
            context = "main"


        if new_command_name in all_commands:
            print("ERROR: command already exists")
            return

        structure = {"command": command_code, "description": ""}

        if context not in commands_by_context:
            commands_by_context[context] = {}

        commands_by_context[context][new_command_name] = structure

        sorted_json = json.dumps(commands_by_context[context], sort_keys=True, indent=2)
        f = open(os.path.join(CONF_DIRECTORY, context + ".json"), "w")
        f.write(sorted_json)

        print(f"command {new_command_name} succesfully created")

        return


    #TODO: add delete command for commands

    print("ERROR: unknown ct command")


def handle_py_command(arguments):

    #TODO: we might need 2 commands, one for streaming (pipe in, pipe out)
    #      and one for "collect all input first"

    python_code = " ".join(arguments)

    all_lines = []
    for line in sys.stdin:
        line = line.strip()
        all_lines.append(line) #TODO: all_lines should be available as "al" with a slightly different command, might be more useful in general (list comprehension over "al")
        
        try:
            eval(python_code, {}, {"i": line})
        except Exception as e:
            print("Error in python code:", e)


def execute_command(arguments, commands, commands_by_context):
    if not arguments:
        print("Enter a command, use \"ct list\" for a list of commands")
        return

    main_command = arguments[0]
    arguments = arguments[1:]

    if main_command == "ct":
        handle_ct_command(arguments, commands, commands_by_context)
        return

    if main_command == "py":
        handle_py_command(arguments)
        return

    if main_command.strip() in commands:
        command_data = commands[main_command]
        command_template = command_data["command"]
        
        if "[]" in command_template:
            command_to_execute = command_template.replace("[]", " ".join(arguments))
        elif "[1]" in command_template:
            nr_arguments = len(arguments)
            current_template_argument = 1
            while current_template_argument <= nr_arguments:
                placeholder = f"[{current_template_argument}]" 
                if placeholder not in command_template:
                    print(f"WARNING: arguments were ignored, command only takes {current_template_argument-1}, {nr_arguments} were provided")
                    break
                command_template = command_template.replace(placeholder, arguments[current_template_argument - 1])
                current_template_argument += 1
            if f"[{current_template_argument}]" in command_template: 
                print(f"ERROR: no argument was supplied for argument {current_template_argument}, but the command needs it")
                return
            command_to_execute = command_template

        print("(" + command_to_execute + ")") #TODO: make this print conditional on config
    
        #TODO: the below might not work with piping in data, we probably need subprocess for that
        os.system(command_to_execute)
        return

    print("ERROR: unknown command")


if __name__ == "__main__":
    commands, commands_by_context = load_commands()
    execute_command(sys.argv[1:], commands, commands_by_context)

