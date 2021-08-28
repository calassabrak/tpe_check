# TPEScout
This program searches for posts in certain [ISFL](https://forums.sim-football.com/) subforums to quantify the activity levels of certain subsets of users.

# Motivation
The ISFL is a simulation sports league in which users take on the role of football players and compete against teams composed of other users on the website. Users can improve their player by completing a variety of activities on the forum. Each of the league's 22 teams is managed by a pair of users ('general managers' or 'GMs'), and they are the primary audience for this program.

Every offseason (roughly every eight weeks) the league typically recruits 40 to 60 new users, and GMs are individually responsible for researching and scouting how well the users' players are performing prior to the offseason draft. GMs *do not* have a built-in way to confirm a user's progress and must manually search through each user's activity to obtain this information. As a former GM of one of these teams, I wanted to automate this process as a time-saving measure. 

# How to Use?
URLs embedded in main.py are static and should not need to be updated to run the program. The program does rely on associated files uploaded to Github, so users may need to update the directory paths after downloading. Due to the forum rate limiting searches to every ten seconds, the program will take approximately five minutes to return  the final data frame in /output.csv.

An example of the resulting data frame can be seen below after being exported to Tableau, and the full dashboard itself can be located [here](https://public.tableau.com/app/profile/justin.pruitt/viz/ScoutingS32/Dashboard1).
![Tableau Dashboard](https://i.imgur.com/AbQDMCp.png)
