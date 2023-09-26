#!/bin/bash

git pull origin main
git submodule foreach 'git pull origin main'