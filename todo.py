from os import path
import sys
import os
import argparse
import re
from datetime import datetime
import shutil
from pathlib import Path

# TODO: Add archiving
# TODO: Add editing of other things than descrip


class TodoPrinter:
    def __init__(self, props=None):
        self.color = False
        self.delim = '|'
        props = props if props else TodoPrinter.Properties.get_default()
        self.set_props(props)

    class Property:
        def __init__(self, show, width, name, t, print_format=None):
            self.show = show
            self.width = width
            self.name = name
            self.type = t
            self.print_format = print_format if print_format else '{:' + str(
                width) + '.' + str(width) + 's}'

    class Properties:
        def __init__(self):
            # Order: | idx | done | done_date | priority | due_date | created_date | description | categories | projects | labels |
            self.idx = TodoPrinter.Property(False, 3, 'Idx', int)
            self.done = TodoPrinter.Property(False, 5, 'Done', bool)
            self.done_date = TodoPrinter.Property(False, 10, 'Completed',
                                                  datetime)
            self.prio = TodoPrinter.Property(False, 5, 'Prio', str,
                                             ' ({:1.1s}) ')
            self.due = TodoPrinter.Property(False, 10, 'Due', datetime)
            self.created_date = TodoPrinter.Property(False, 10, 'Created',
                                                     datetime)
            self.description = TodoPrinter.Property(False, 30, 'Description',
                                                    str)
            self.categories = TodoPrinter.Property(False, 10, 'Categories',
                                                   list)
            self.projects = TodoPrinter.Property(False, 10, 'Projects', list)
            self.labels = TodoPrinter.Property(False, 15, 'Labels', dict)

        def get_default():
            return TodoPrinter.Properties().show_idx().show_prio().show_due(
            ).show_description().show_categories().show_projects()

        def show_labels(self):
            self.labels.show = True
            return self

        def show_due(self):
            self.due.show = True
            return self

        def show_done_date(self):
            self.done_date.show = True
            return self

        def show_done(self):
            self.done.show = True
            return self

        def show_created_date(self):
            self.created_date.show = True
            return self

        def show_prio(self):
            self.prio.show = True
            return self

        def show_projects(self):
            self.projects.show = True
            return self

        def show_categories(self):
            self.categories.show = True
            return self

        def show_description(self):
            self.description.show = True
            return self

        def show_idx(self):
            self.idx.show = True
            return self

    class Line:
        def __init__(self, todo, keys, props):
            (self.rows,
             self.dict) = TodoPrinter.Line.create_line(todo, keys, props)

        def split_line(string, width):
            lines = [''] * (1 + len(string.rstrip()) // width)
            words = string.rstrip().split(' ')
            words.reverse()
            acc = 0
            while len(words):
                word = words.pop()
                acc += len(word)
                lines[acc // width] += (word + ' ')
                acc += 1
            return lines

        def create_line(todo, keys, props):
            value_list_dict = {}
            rows = 0
            for key in keys:
                value_list_dict[key] = []
                value = ''
                if key in todo.__dict__.keys():
                    value = todo.__dict__[key]
                elif key in todo.labels.keys():
                    value = todo.labels[key]

                prop = props.__dict__[key]
                if value is None:
                    value_list_dict[key] = ['']
                elif prop.type is str:
                    value_list_dict[key] = TodoPrinter.Line.split_line(
                        value, prop.width)
                elif prop.type is int:
                    value_list_dict[key] = [str(value).rjust(prop.width)]
                elif prop.type is datetime:
                    value_list_dict[key] = [value.date().isoformat()]
                elif prop.type is list:
                    value_list_dict[key] = [str(v) for v in value]
                elif prop.type is bool:
                    value_list_dict[key] = [' (X) ' if value else '']
                else:
                    value_list_dict[key] = [str(value)]
                rows = max(rows, len(value_list_dict[key]))
            return (rows, value_list_dict)

        def get_value(self, key, idx):
            if (idx < len(self.dict[key])):
                return self.dict[key][idx]
            return None

        def get_rows(self):
            return self.rows

    def set_props(self, props):
        self.props = props
        self.keys = [
            key for key, value in self.props.__dict__.items() if value.show
        ]
        self.title_format = self.create_title_format()
        self.format = self.create_format()

    def create_title_format(self):
        format_str = '| '
        for key in self.keys:
            value = self.props.__dict__[key]
            format_str += '{:' + str(value.width) + \
                '.' + str(value.width) + 's} | '
        return format_str.rstrip()

    def create_format(self):
        format_str = '| '
        for key in self.keys:
            value = self.props.__dict__[key]
            format_str += value.print_format + ' | '
        return format_str.rstrip()

    def print_title(self):
        title = ()
        for key in self.keys:
            title += (self.props.__dict__[key].name, )
        title_str = self.title_format.format(*title)
        print('=' * len(title_str))
        print(title_str)
        print('=' * len(title_str))

    def print_todo(self, todo):
        line = TodoPrinter.Line(todo, self.keys, self.props)
        self.print_line(line)
        return

    def print_line(self, line, border=False):
        for row in range(0, line.rows):
            # Gather all the values to print
            values = ()
            for key in self.keys:
                value = line.get_value(key, row)
                if type(value) is str:
                    values += (value, )
                elif value is None:
                    values += ('', )
                else:
                    print('Unrecognized value type {}', value.type)
                    values += ('', )
            if row == 0:
                print(self.format.format(*values))
            else:
                print(self.title_format.format(*values))

    def print_horizontal_separator(self):
        print('-' * len(self.format.format(*('', ) * (len(self.keys)))))

    def print_todos(self, todos):
        self.print_title()
        for todo in todos:
            self.print_todo(todo)
            self.print_horizontal_separator()


class Todo:
    def __init__(self, description):
        self.done = False
        self.idx = None
        self.description = description
        self.categories = []
        self.projects = []
        self.prio = None
        self.created_date = None
        self.done_date = None
        self.due = None
        self.labels = {}
        self.matched = True
        self.line = ''

    def add_category(self, category):
        self.categories.append(category)

    def add_project(self, project):
        self.projects.append(project)

    def set_idx(self, idx):
        self.idx = idx

    def set_prio(self, prio):
        self.prio = prio

    def set_created(self, date):
        self.created_date = date

    def set_done(self, done):
        self.done = done
        self.done_date = datetime.today() if (self.done
                                              and self.created_date) else None

    def toggle_done(self):
        self.set_done(not self.done)

    def set_done_date(self, date):
        self.done_date = date

    def set_due(self, date):
        self.due = date

    def add_label(self, key, value):
        self.labels[key] = value

    def __str__(self):
        ret = ''
        if self.matched:
            if self.done:
                ret += 'x '
            if self.prio:
                ret += '({}) '.format(self.prio)
            if self.done_date:
                ret += '{} '.format(self.done_date.date().isoformat())
            if self.created_date:
                ret += '{} '.format(self.created_date.date().isoformat())

            ret += '{} '.format(self.description)

            for p in self.projects:
                ret += '+{} '.format(p)

            for c in self.categories:
                ret += '@{} '.format(c)

            for (key, value) in self.labels.items():
                ret += '{}:{} '.format(key, value)

            if self.due:
                ret += 'due:{}'.format(self.due.date().isoformat())

            ret += '\n'
        else:
            ret = self.line

        return ret


class Dotfile:
    def __init__(self, filename):
        self.show_default = []
        self.custom_labels = {}
        self.todo_path = None
        self.read_dotfile(filename)

    def read_dotfile(self, filename):
        if Path(filename).is_file():
            pattern = re.compile(r'(.+)=(.+)', re.MULTILINE | re.DOTALL)
            with open(filename, 'r') as dotfile:
                for line in dotfile.readlines():
                    match = pattern.match(line)
                    if match:
                        prop = match.group(1).strip()

                        if prop == 'show-default':
                            self.show_default = [
                                s.strip() for s in match.group(2).split(',')
                            ]
                        elif prop == 'custom-labels':
                            self.handle_custom_label(match.group(2))
                        elif prop == 'todo-dir':
                            self.todo_path = match.group(
                                2) + os.path.sep + 'todo.txt'

            print('[DEBUG]: show_default = {}'.format(self.show_default))
            print('[DEBUG]: custom_labels = {}'.format(self.custom_labels))
            print('[DEBUG]: todo_path = {}'.format(self.todo_path))
        else:
            print('[DEBUG]: No dotfile exists')

        if not self.todo_path:
            self.todo_path = os.path.expanduser('~') + os.path.sep + 'todo.txt'

    def handle_custom_label(self, label_str):
        for match in re.finditer(r'(\{[^\}]*\})', label_str):
            fields = re.search(
                r'id:\s*([A-Za-z0-9_]+),\s*width:\s*(\d+),\s*name:\s*([A-Za-z0-9_]+),\s*type:\s*([A-Za-z]+)',
                match.group(0), re.MULTILINE | re.DOTALL)
            if fields:
                self.custom_labels[fields.group(1)] = TodoPrinter.Property(
                    False, int(fields.group(2)), fields.group(3),
                    fields.group(4))


def create_todofile(file_path):
    if input(
            '{} does not exist. Do you wish to create an empty todo.txt file at this location? (y/n): '
            .format(file_path)) == 'y':
        try:
            f = open(file_path, 'w+')
            f.close()
        except IOError:
            print('Failed to create todo.txt file at {}'.format(file_path))
            return False
    else:
        return False

    return True


def load_todos(config):
    if not Path(config.todo_path).is_file() and not create_todofile(
            config.todo_path):
        return []

    todos = []
    with open(os.path.expanduser('~') + '/' + 'todo.txt', 'r+') as todo_file:
        for idx, line in enumerate(todo_file.readlines()):
            try:
                match = re.match(
                    r'(x )?(\([A-Z]\) )?([0-9]{4}-[0-9]{2}-[0-9]{2} )?([0-9]{4}-[0-9]{2}-[0-9]{2} )?(.*)',
                    line)
                if match:
                    # Remove all categories, projects and custom labels
                    description = re.sub(
                        r'\s(\+[A-Za-z0-9\-_]+)|(@[A-Za-z0-9\-_]+)', ' ',
                        match.group(5))
                    description = re.sub(
                        r'\s[A-Za-z0-9\-_]+[:]{1}[A-Za-z0-9\-_]+', ' ',
                        description)

                    todo = Todo(description.strip())
                    todo.set_idx(idx)

                    if match.group(2):
                        todo.set_prio(match.group(2)[1])

                    # Match dates, categories, projects and custom labels
                    if match.group(1):  # Marks done
                        todo.set_done(True)
                        if match.group(3):  # One date exists
                            # We are not allowed to have a completed date without a created date
                            if match.group(4):
                                todo.set_done_date(
                                    datetime.strptime(
                                        match.group(3).rstrip(), '%Y-%m-%d'))
                                todo.set_created(
                                    datetime.strptime(
                                        match.group(4).rstrip(), '%Y-%m-%d'))
                            else:
                                raise RuntimeError(
                                    'Todo marked as done but has ONE date (should have 2 or none): "{}"'
                                    .format(line.rstrip()))
                    else:
                        if match.group(3) and not match.group(4):
                            todo.set_created(
                                datetime.strptime(
                                    match.group(3).rstrip(), '%Y-%m-%d'))
                        elif match.group(4):
                            raise RuntimeError(
                                'Todo is not marked as done but has 2 dates: "{}"'
                                .format(line.rstrip()))
                    category_match = re.findall(r'\s\@[A-Za-z0-9_\-]+',
                                                match.group(5))
                    for category in category_match:
                        todo.add_category(category.strip()[1:])

                    project_match = re.findall(r'\s\+[A-Za-z0-9_\-]+',
                                               match.group(5))

                    for project in project_match:
                        todo.add_project(project.strip()[1:])

                    label_match = re.findall(
                        r'\s[A-Za-z0-9\-_]+[:]{1}[A-Za-z0-9\-_]+',
                        match.group(5))

                    for label in label_match:
                        key, value = tuple(label.strip().split(':'))
                        if key == 'due':
                            todo.set_due(datetime.strptime(value, '%Y-%m-%d'))
                        else:
                            todo.add_label(key, value)

                    todos.append(todo)
                else:
                    raise RuntimeError('Could not match line: {}'.format(
                        line.rstrip()))
            except RuntimeError as err:
                todo.matched = False
                todo.line = line
                todos.append(todo)
                print('[WARN] {}'.format(err))

    return todos


def write_todo_file(config, todos):
    temp_path = os.path.basename(config.todo_path) + '~todo.txt'
    try:
        with open(temp_path, 'w+') as todo_file:
            for todo in todos:
                todo_file.write(str(todo))
    except:
        print("Failed to write content to todo.txt tmp file")
        exit()

    try:
        shutil.move(temp_path, config.todo_path)
    except:
        print("Failed to overwrite todo.txt with modifications")
        exit()


def add_todo(config, prio, created_date, description, projects, categories,
             due):
    todo = Todo(description)

    for c in categories:
        todo.add_category(c)

    todo.set_created(created_date)
    todo.set_prio(prio)

    for p in projects:
        todo.add_project(p)

    todo.set_due(due)

    with open(config.todo_path, 'a+') as todo_file:
        todo_file.write(str(todo))


def ls_todo(config, category, project, due, finished):
    todos = load_todos(config)
    filtered = []
    for todo in todos:
        include = todo.matched
        # check for category
        if category:
            include = include and category in todo.categories
        # check for project
        if project:
            include = include and project in todo.projects
        # check for due
        if due:
            if todo.due:
                include = include and todo.due.date() <= due.date()
            else:
                include = False
        # check for finished
        if not finished:
            include = include and not todo.done

        if include:
            filtered.append(todo)

    filtered.sort(key=lambda t: t.due if t.due else datetime.max)
    filtered.sort(key=lambda t: t.prio if t.prio else 'Z')

    props = TodoPrinter.Properties()
    for k, v in config.custom_labels.items():
        props.__dict__[k] = v

    if len(config.show_default) > 0:
        for field in config.show_default:
            if field in props.__dict__:
                props.__dict__[field].show = True
    else:
        props = TodoPrinter.Properties.get_default()

    printer = TodoPrinter(props)
    printer.print_todos(filtered)

    return


def get_todo_from_line(todos, line):
    idx_ = [idx for idx, value in enumerate(todos) if idx == int(line)]

    if len(idx_) > 0:
        idx = idx_[0]
        return todos[idx]
    else:
        print('No match for line no: {}'.format(line))


def remove_todo(config, line):
    todos = load_todos(config)
    todo = [get_todo_from_line(todos, line)]

    printer = TodoPrinter(
        TodoPrinter.Properties.get_default().show_done().show_done_date())
    printer.print_todos(todo)

    c = input('Are you sure you want to PERMANENTLY remove this Todo? (y/n): ')
    if c == 'y':
        todos = filter(lambda t: t.idx != int(line), todos)
        write_todo_file(config, todos)


def edit_todo(config, line, description):
    todos = load_todos(config)
    todo = get_todo_from_line(todos, line)
    if todo:
        todo.set_description(description)
        write_todo_file(todos)
    return


def toggle_todo(config, line, status):
    todos = load_todos(config)
    todo = get_todo_from_line(todos, line)
    if todo:
        if status == 'done':
            todo.set_done(True)
        elif status == 'ongoing':
            todo.set_done(False)
        elif status == 'toggle':
            todo.toggle_done()
        else:
            print('Unrecognized status')
            exit()
        write_todo_file(todos)


def main():
    parser = argparse.ArgumentParser(description='Todo.txt CLI')

    subparsers = parser.add_subparsers(help='sub-command help', dest='cmd')

    # todo add
    add_parser = subparsers.add_parser('add', help='Add todo')
    add_parser.add_argument('description',
                            type=str,
                            help='Description of todo')
    add_parser.add_argument('-t',
                            '--today',
                            dest='today',
                            action='store_true',
                            help='Include created date',
                            required=False)
    add_parser.add_argument('-d',
                            metavar='due',
                            dest='due',
                            type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                            action='store',
                            help='Set due date',
                            required=False)
    add_parser.add_argument('-@',
                            metavar='category',
                            dest='category',
                            default=[],
                            type=lambda s: s.split(','),
                            action='store',
                            help='Set categories, separated by commas')
    add_parser.add_argument('-+',
                            metavar='project',
                            dest='project',
                            default=[],
                            type=lambda s: s.split(','),
                            action='store',
                            help='Set projects, separated by commas')
    add_parser.add_argument('-p',
                            metavar='priority',
                            dest='prio',
                            type=lambda s: s.upper()[0],
                            action='store',
                            help='Set priority')

    # todo ls
    ls_parser = subparsers.add_parser('ls', help='List todo')
    ls_parser.add_argument('-@',
                           metavar='category',
                           dest='category',
                           action='store',
                           help='Match specified category')
    ls_parser.add_argument('-+',
                           metavar='project',
                           dest='project',
                           action='store',
                           help='Match specified project')
    ls_parser.add_argument(
        '-d',
        metavar='due',
        dest='due',
        type=lambda s: datetime.today()
        if s == 'today' else datetime.strptime(s, '%Y-%m-%d'),
        action='store',
        help='Show only items due by specified day')
    ls_parser.add_argument('-f',
                           '--finished',
                           dest='finished',
                           action='store_true',
                           help='Include finished items')

    # todo rm
    rm_parser = subparsers.add_parser('rm', help='Remove todo')
    rm_parser.add_argument('line',
                           type=str,
                           help='The line no of the todo to remove',
                           action='store')
    edit_parser = subparsers.add_parser('edit', help='Edit todo')

    edit_parser.add_argument('line',
                             type=str,
                             help='The line no of the todo to edit',
                             action='store')
    edit_parser.add_argument('description',
                             type=str,
                             help='New description of todo')

    # todo set
    set_parser = subparsers.add_parser('set', help='Toggle status of todo')
    set_parser.add_argument('line',
                            type=str,
                            help='The line of the todo to toggle',
                            action='store')
    set_parser.add_argument('status', choices=['done', 'ongoing', 'toggle'])
    args = parser.parse_args(sys.argv[1:])

    config = Dotfile(os.path.expanduser('~') + '/' + '.todo-cli')

    if args.cmd == 'add':
        add_todo(config, args.prio,
                 datetime.today() if args.today else None, args.description,
                 args.project, args.category, args.due)
    elif args.cmd == 'ls':
        ls_todo(config, args.category, args.project, args.due, args.finished)
    elif args.cmd == 'rm':
        remove_todo(config, args.line)
    elif args.cmd == 'edit':
        edit_todo(config, args.line, args.description)
    elif args.cmd == 'set':
        toggle_todo(config, args.line, args.status)
    else:
        print(parser.print_help())
        return


if __name__ == "__main__":
    main()
