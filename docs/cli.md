# Flask CLI Reference

Management commands for the Treasure Hunt admin. All commands run inside the
project directory and require the virtual environment to be active.

```bash
cd /home/alphaf42/treasure-hunt
source .venv/bin/activate
```

If `FLASK_APP` is not already set in your environment, prefix every command:

```bash
FLASK_APP=app:create_app flask <command>
```

---

## `flask user` — User Management

### List all users

```bash
flask user list
```

Prints a table of every user with their ID, username, email, role, active
status, and current online status. Admin accounts are highlighted.

---

### Reset a password

```bash
flask user reset-password <username>
```

Prompts for the new password (and confirmation) without echoing it to the
terminal, so it never appears in shell history.

```bash
# Example
flask user reset-password admin
# New password:
# Repeat for confirmation:
```

To pass the password non-interactively (e.g. in a script):

```bash
flask user reset-password admin --password 'NewPass123'
```

Resets the password, invalidates any active session, and marks the user
offline so the new password takes effect immediately.

---

### Create a new admin user

```bash
flask user create-admin <username> <email>
```

Creates a brand-new user with admin rights. Prompts for a password
interactively.

```bash
# Example
flask user create-admin superadmin superadmin@example.com
# Password:
# Repeat for confirmation:
```

Fails with an error if the username or email is already taken.

---

### Promote a user to admin

```bash
flask user promote <username>
```

Grants admin rights to an existing regular user.

```bash
# Example
flask user promote ranjith
```

---

### Remove admin rights

```bash
flask user demote <username>
```

Removes admin rights from an admin user. Blocked if the target is the
**last remaining admin** to prevent accidental lockout.

```bash
# Example
flask user demote ranjith
```

---

### Deactivate a user account

```bash
flask user deactivate <username>
```

Disables the account so the user cannot log in. Their data is preserved.
Also invalidates any active session immediately. Cannot be used on admin
accounts via CLI.

```bash
# Example
flask user deactivate baduser
```

---

### Reactivate a user account

```bash
flask user activate <username>
```

Re-enables a previously deactivated account.

```bash
# Example
flask user activate baduser
```

---

## Quick-reference table

| Command | Arguments | What it does |
|---|---|---|
| `flask user list` | — | List all users |
| `flask user reset-password` | `<username>` | Reset a user's password |
| `flask user create-admin` | `<username> <email>` | Create a new admin user |
| `flask user promote` | `<username>` | Grant admin rights |
| `flask user demote` | `<username>` | Remove admin rights |
| `flask user deactivate` | `<username>` | Disable an account |
| `flask user activate` | `<username>` | Re-enable an account |

---

## Getting help

Every command supports `--help`:

```bash
flask user --help
flask user reset-password --help
```
