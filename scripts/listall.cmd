@echo off
listall.py -d . -xd .git -xd *cache* -xd *egg* -xd revisions -xd *.*~ -fmt summary %*
