### Modules ###

# Backend module, with recipes for managing the server, DB...
mod backend

# Frontend module, with recipes for managing the frontend server, ...
mod frontend

### Aliases ###

# Backend recipes
alias run-db := backend::run-db
alias serve := backend::serve
alias revision := backend::revision
alias migrate := backend::migrate

# Frontend recipes
alias front := frontend::front

# DB recipes
alias db := run-db

# Git recipes
alias ga := git-add

### Recipes ###

# List available commands (default)
[default]
@list:
    just --list

# git add
git-add *ARGS="-p":
    git add {{ARGS}}

# Run full local setup (back+front+db)
run:
    just serve & just front
    wait
