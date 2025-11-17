# **dR-mentions**

`dr-mentions` is a small Python "daemon" that uses retoor's devRant RSS feed for monitoring new mentions. When your username appears in a new comment, the script notifies you — either through **desktop notifications** (GUI mode) or **terminal output** (CLI mode). GUI mode is the intended mode and CLI mode is more half-assed and was made on a whim.

It is intended to be run as a **user-level systemd service**, but can also be used manually on the command line.

---

## Installation

Download the latest release from the `Releases` page and unpack it where you want or clone the git repository directly with:
```bash
git clone <whatever here>
```
cd into the newly extracted or cloned project directory and run the `install.sh` script:
```bash
cd dr-mentions
chmod +x install.sh
sudo ./install.sh
```

This installs:

| Component                   | Installed To                                  |
| --------------------------- | --------------------------------------------- |
| Python app + `.venv`        | `/usr/share/dr-mentions/`                     |
| Systemd user service        | `/usr/lib/systemd/user/dr-mentiond.service`   |
| Run script (`dr-mentiond`)  | `/usr/bin/dr-mentiond`                        |


After installation and **before usage**, you must initialize a config file for the script, containing your username and optional subscribes(non-functional currently) with:

```bash
dr-mentiond --init
```

(On the first run, or if the config doesn't exist/got deleted, you can run `dr-mentiond` without options and it will default to initializing a new config)

The initialization is interactive and straightforward, so just follow the instructions of the script.

---
## Usage

After installing and running `dr-mentiond --init` you can start using the script. The script can be run from the **terminal** or as a **daemon service**. Running as a service is the intended way.

Running `dr-mentiond` without any options starts the script which begins periodically polling retoor's RSS feed *(at https://static.molodetz.nl/dr.mentions.xml)*, and listening to the updates(new mentions). If any of the new mentioned since the previous poll are mentioning the username you have specified in your config, the script will send a clickable desktop notification informing you that you've been mentioned, by whom, what was the comment, and what's the link to the original rant. Clicking the notification will open the rant in your default browser.

It is also possible to run the script without a config file, supplying all the options as command line arguments with `--no-config` in the following way:

```bash
dr-mentiond --no-config --user <your-username> --subscribe-to <username> --subscribe-to <username2> --subscribe-to ...
```

Where `--user` specifies your username and `--subscribes-to` specifies usernames of ranters for whom you want to get **'New Rant'** notifications(not yet implemented)

To have the script stay in the background and notify you whenever a new mention of you has been posted, you must activate the **user-level service**:

```bash
systemctl --user daemon-reload
systemctl --user enable --now dr-mentiond.service
```

---

## Dependencies

* `desktop-notifier`
* `feedparser`
* `platformdirs`
* `requests`

---

## Acknowledgments
Special thanks to retoor for the RSS feed and to all the other people who try to keep this dead platform alive with random Frankenstein solutions
