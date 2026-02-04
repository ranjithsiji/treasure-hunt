# Treasure Hunt Management System

A comprehensive Flask-based treasure hunt game management system with MariaDB database, Bootstrap CSS framework, and jQuery for interactive features.

## Features

### Admin Features
1. **Game Initialization**
   - Set number of teams
   - Set number of levels
   - Set number of questions per level
   - Define teams passing criteria per level
   - Set number of clues available per team
   - Mark final level

2. **Level Management**
   - Create and manage multiple levels
   - Start/Stop levels
   - Add questions (Text, Image, Video) with answers
   - Add multiple clues for each question

3. **Team Management**
   - Create and delete teams
   - View team progress
   - Monitor team statistics

4. **User Management**
   - View all registered users
   - Assign users to teams
   - Manage user access

5. **Admin Dashboard**
   - Overview of game status
   - Quick access to all management features
   - Real-time statistics

### User Features
1. **Registration & Login**
   - User registration system
   - Secure login with password hashing
   - Team assignment

2. **Game Play**
   - Answer questions to progress
   - Request clues when stuck
   - View current question with media (images/videos)
   - Real-time answer validation

3. **Team Features**
   - Join existing teams
   - View team members
   - Track team progress

4. **Scoreboard**
   - Public scoreboard showing all teams
   - Rankings based on level, questions completed, and time
   - Real-time updates

### Game Mechanics
- Teams progress through multiple levels
- Each level contains multiple questions
- Questions can include text, images, or videos
- Teams can use limited clues to help solve questions
- Time tracking for each question and level
- Levels freeze after completion until admin starts next level
- First team to complete all levels wins

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MariaDB with PyMySQL
- **Frontend**: Bootstrap 5
- **JavaScript**: jQuery
- **Package Manager**: uv
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF

## Installation

### Prerequisites
- Python 3.8+
- MariaDB/MySQL server
- uv package manager

### Setup Instructions

1. **Clone or navigate to the project directory**
   ```bash
   cd /home/alphaf42/treasure-hunt
   ```

2. **Install uv (if not already installed)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Create virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   
   uv pip install -r requirements.txt
   ```

4. **Configure Database**
   
   Create a MariaDB database:
   ```sql
   CREATE DATABASE treasure_hunt;
   CREATE USER 'treasure_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON treasure_hunt.* TO 'treasure_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

5. **Update Environment Variables**
   
   Edit `.env` file:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-change-this-in-production
   DATABASE_URI=mysql+pymysql://treasure_user:your_password@localhost/treasure_hunt
   ```

6. **Initialize Database**
   ```bash
   uv run python init_db.py
   ```

7. **Run the Application**
   ```bash
   uv run python app.py
   ```

8. **Access the Application**
   
   Open your browser and navigate to: `http://localhost:5000`

## Default Admin Credentials

- **Username**: admin
- **Password**: admin123

⚠️ **IMPORTANT**: Change the admin password immediately after first login!

## Usage Guide

### For Administrators

1. **Login** with admin credentials
2. **Initialize Game**:
   - Go to Admin Dashboard
   - Click "Initialize Game"
   - Set game parameters (teams, levels, questions, clues)
   
3. **Create Teams**:
   - Navigate to "Manage Teams"
   - Create teams for participants
   
4. **Add Questions**:
   - Go to "Manage Levels"
   - Select a level
   - Add questions with answers
   - Add clues for each question
   
5. **Assign Users to Teams**:
   - Go to "Manage Users"
   - Assign registered users to teams
   
6. **Start Game**:
   - Return to Dashboard
   - Click "Start Game"
   
7. **Manage Levels During Game**:
   - Start/Stop levels as teams progress
   - Monitor team progress on dashboard

### For Players

1. **Register** for an account
2. **Login** with your credentials
3. **Join a Team** (or wait for admin assignment)
4. **Wait** for game to start
5. **Play the Game**:
   - Read questions carefully
   - Use clues if needed (limited supply!)
   - Submit answers
   - Progress through levels
6. **Check Scoreboard** to see rankings

## Project Structure

```
treasure-hunt/
├── app.py                 # Main application file
├── models.py              # Database models
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── routes/               # Route blueprints
│   ├── auth.py          # Authentication routes
│   ├── admin.py         # Admin routes
│   ├── game.py          # Game routes
│   └── public.py        # Public routes
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── admin/           # Admin templates
│   ├── game/            # Game templates
│   └── public/          # Public templates
└── static/              # Static files
    ├── css/            # Stylesheets
    ├── js/             # JavaScript files
    └── uploads/        # Uploaded media files
```

## Database Schema

### Tables
- **users**: User accounts and authentication
- **teams**: Team information and progress
- **game_config**: Game configuration and settings
- **levels**: Level definitions
- **questions**: Questions for each level
- **clues**: Clues for questions
- **team_progress**: Team progress tracking
- **clue_usage**: Clue usage tracking

## Features in Detail

### Question Types
1. **Text**: Plain text questions
2. **Image**: Questions with image attachments
3. **Video**: Questions with video attachments

### Scoring System
Teams are ranked by:
1. Current level (higher is better)
2. Number of completed questions (more is better)
3. Total time taken (less is better)

### Time Tracking
- System tracks time for each question
- Total time per level is calculated
- Time starts when question is first viewed
- Time stops when correct answer is submitted

## Security Features

- Password hashing using Werkzeug
- Session-based authentication with Flask-Login
- CSRF protection with Flask-WTF
- Admin-only routes protected with decorators
- SQL injection prevention with SQLAlchemy ORM

## Troubleshooting

### Database Connection Issues
- Verify MariaDB is running
- Check DATABASE_URI in .env file
- Ensure database user has proper permissions

### File Upload Issues
- Check `static/uploads` directory exists
- Verify write permissions
- Check MAX_CONTENT_LENGTH setting

### Port Already in Use
- Change port in app.py: `app.run(port=5001)`
- Or kill process using port 5000

## Future Enhancements

- [ ] Email notifications
- [ ] Team chat functionality
- [ ] Question difficulty levels
- [ ] Hints system separate from clues
- [ ] Export game results to CSV/PDF
- [ ] Mobile app version
- [ ] Real-time scoreboard updates with WebSockets
- [ ] Question randomization
- [ ] Multi-language support

## License

This project is open source and available for educational purposes.

## Support

For issues or questions, please contact the administrator.

---

**Enjoy your Treasure Hunt! 🏆**
