*** Comments ***
# Copyright (c) 2014 Sine Nomine Associates
# See LICENSE

*** Settings ***
Library         OperatingSystem
Library         String
Library         OpenAFSLibrary

Suite Setup     Set Test Run Documentation

*** Keywords ***
| Set Test Run Documentation
|  | Set Suite Documentation | OpenAFS Test Run\n\n      | append=False | top=True
|  | Set Suite Documentation | - *Cell:* ${AFS_CELL}\n   | append=True  | top=True
|  | Set Suite Documentation | - *Realm:* ${KRB_REALM}\n | append=True  | top=True
