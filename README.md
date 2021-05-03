# todo-cli

Python implmentation of a Todo.txt CLI using zero dependencies (except for Python3)

![todo-cli](https://github.com/snystedt/todo-cli/blob/main/example.PNG)

## Dotfile

Dotfile currently supports options:

- `show-default`: the default columns for `todo_ls`. Comma-separated list of id:s (`idx`,`done`,`done_date`,`prio`,`due`,`created_date`,`description`,`categories`,`projects`,`labels`) and any custom labels defined below.
- `custom-labels`: custom columns for labels for `todo_ls`. One-line JSON objects with `id` (label used above), `width` (width of rendered column), `name` (column name) and `type` (`int`, `str`)
- `todo-dir`: change default path for `todo.txt` file.

See `todo.cli` for example.
