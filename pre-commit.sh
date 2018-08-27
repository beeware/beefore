#!/bin/bash

touch .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "beekeeper -a pre_commit" > .git/hooks/pre-commit