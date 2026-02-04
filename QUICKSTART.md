# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   
2. **Follow the prompts** to configure your database

3. **Start the application:**
   ```bash
   uv run python app.py
   ```

4. **Open your browser** and go to: http://localhost:5000

5. **Login as admin:**
   - Username: `admin`
   - Password: `admin123`

### Option 2: Manual Setup

1. **Create MariaDB database:**
   ```sql
   CREATE DATABASE treasure_hunt;
   CREATE USER 'treasure_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON treasure_hunt.* TO 'treasure_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Update .env file** with your database credentials

3. **Initialize database:**
   ```bash
   uv run python init_db.py
   ```

4. **Run the application:**
   ```bash
   uv run python app.py
   ```

## 📋 First Time Setup Checklist

### Admin Tasks

- [ ] Login with default admin credentials
- [ ] Change admin password
- [ ] Initialize the game (set parameters)
- [ ] Create teams
- [ ] Add levels and questions
- [ ] Add clues for questions
- [ ] Assign users to teams
- [ ] Start the game

### Player Tasks

- [ ] Register an account
- [ ] Join a team
- [ ] Wait for game to start
- [ ] Start playing!

## 🎮 Game Flow

1. **Admin initializes game** → Sets all parameters
2. **Admin creates teams** → Teams are ready for players
3. **Players register** → Create accounts
4. **Players join teams** → Or admin assigns them
5. **Admin starts game** → Level 1 becomes active
6. **Teams play Level 1** → Answer questions, use clues
7. **Teams complete Level 1** → Wait for next level
8. **Admin starts Level 2** → Process repeats
9. **First team completes final level** → Wins the treasure hunt!

## 🔧 Common Commands

```bash
# Install dependencies
uv pip install -r requirements.txt

# Initialize database
uv run python init_db.py

# Run application
uv run python app.py

# Run on different port
# Edit app.py and change: app.run(port=5001)
```

## 📱 Access Points

- **Home Page**: http://localhost:5000
- **Login**: http://localhost:5000/auth/login
- **Register**: http://localhost:5000/auth/register
- **Admin Dashboard**: http://localhost:5000/admin/dashboard
- **Game Dashboard**: http://localhost:5000/game/dashboard
- **Scoreboard**: http://localhost:5000/game/scoreboard

## 🎯 Sample Game Setup

Here's a quick example to get you started:

### Game Configuration
- Number of Teams: 4
- Number of Levels: 3
- Questions per Level: 5
- Teams Passing per Level: 2
- Clues per Team: 10

### Sample Question (Level 1, Question 1)
- **Type**: Text
- **Question**: "What has keys but no locks, space but no room, and you can enter but can't go inside?"
- **Answer**: "keyboard"
- **Clue 1**: "You use it every day with your computer"
- **Clue 2**: "It has letters and numbers on it"

## ⚠️ Important Notes

1. **Change default admin password** immediately after first login
2. **Backup your database** regularly
3. **Don't delete teams** that have active players
4. **Test questions** before starting the game
5. **Monitor the scoreboard** during gameplay

## 🆘 Troubleshooting

### Can't connect to database?
- Check if MariaDB is running: `sudo systemctl status mariadb`
- Verify credentials in `.env` file
- Test connection: `mysql -u treasure_user -p treasure_hunt`

### Port 5000 already in use?
- Change port in `app.py`: `app.run(port=5001)`
- Or kill the process: `sudo lsof -ti:5000 | xargs kill -9`

### File upload not working?
- Check `static/uploads` directory exists
- Verify write permissions: `chmod 755 static/uploads`

## 🎉 Ready to Play!

Your treasure hunt system is now ready. Have fun creating an exciting game for your participants!

For detailed documentation, see [README.md](README.md)
