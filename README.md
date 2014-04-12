Introduction
============

This is the development buildout for xpose414 site.

In order to bootstrap a development environment just do

```bash
$ ~/python/bin/virtualenv-2.7 xpose
$ cd ./xpose
$ python bootstrap.py -c development.cfg
$ bin/buildout -c develoment.cfg
```

Setup API Access
----------------

In order to access external APIs ou need to authenticate with the services. For
GA access the following details are required:

```json
{
  "installed": {
    "client_id": "[[INSERT CLIENT ID HERE]]",
    "client_secret": "[[INSERT CLIENT SECRET HERE]]",
    "redirect_uris": [],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}
```

Xovi API paramters:

```
    'key'     => 'myPersonalKey',
    'service' => 'user',
    'method'  => 'getCreditState',
    'format'  => 'json',
``

// Dashboard definitions seotool (monthly)

monthly - 1. des Folgemonats


- Besucherinformationen

* anzahl user organisch
* visits
* aufenthaltsdauer
* absprungrate
* seiten pro besuch
* neue besuche

- XOVI

* Fokus Keywords
* Group eruiren (daten)


- ACtive Collab

* stunden/bearbeiter/datum/task
* linkliste import csv/excel 


-> Add user and dashboard in one shot!!!

08.01. 16:00 Uhr
15. Januar obacht

wLe9Nky!y0o$w.ea%5$f





