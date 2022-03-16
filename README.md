# Sublime Text Remote Open Extension
Open files remotely from Sublime Text via SSH (SCP)!

Requires Sublime Text 4 build 4075 or newer.

## Limitations

As this extension was developed in a hurry, there are significant limitations:

- Opened remote files are read-only.
- Passwords and any form of interactive authentication methods are not supported.
- Not possible to cancel in-progress operation.
- Only tested on Unix based systems (macOS/Linux).
- Uses the `scp` command, therefore the client must have OpenSSH client installed and the server must support `scp`.
- Only single instance of the same file can open.

These limitations will be fixed in future commits.

## Installation

Simply `git clone` this repo to Sublime Text's package directory! The `main` branch will track a stable version of this extension.

- On macOS, it is located in `~/Library/Application Support/Sublime Text/Packages`.
- On Linux, it is located in `!/.config/sublime-text-3/Packages`

## Usage

- Open the Sublime Text's Command Palette (<kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> or <kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> by default), and select **Remote Open: Open File using SSH**.
- Enter the remote path that you want to open, in form of `<host>:<path>`.
  - `<host>` can be either `hostname` only or `username@hostname`.
  - `<path>` is the absolute path of remote file.
  - The `<host>` part can be omitted in subsequent remote file open *in the same Sublime Text window*. This will use the last used `<host>`.
- To copy the full path of remote file, right click on the tab and select **Copy Remote Path**.
