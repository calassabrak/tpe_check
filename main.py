import csv, pandas as pd, os, re, requests, time, json
from bs4 import BeautifulSoup

# User should specify a 'season' (i.e. 'S32') indicating a specific class of users to check.
season = ['S32']

# User should specify a number of weeks (including current week) to check for various claims.
weeks = 3

########################################################################################################################
# First, retrieve player data from tracker in JSON format and filter by provided season.
tracker_json = requests.get('https://tracker.sim-football.com/players_json').json()
tracker = pd.json_normalize(tracker_json)
users = list(tracker[tracker['draftYear'] == season[0]]['user'])
user_table = pd.DataFrame(users, columns=['Username'])

# Find the current AC number. This is anchored to a known date but is adjusted by the current calendar.
current_AC = 221
AC_start = pd.Timestamp('2021-08-09')
today = pd.Timestamp.today()
weekdiff = int((today - AC_start).days / 7)
current_AC += weekdiff
AC_list = list(range(current_AC - (weeks - 1), current_AC + 1))

# Check local files for awarded TPE.
def ClaimThread(x):
    tpedir = r'C:\Users\GenworthOEM\PycharmProjects\TPEScout\claims'
    for user in x:
        for file in os.listdir(tpedir):
            tpe_check = pd.read_csv('claims/' + file, sep=',', names=['Username','TPE'])
            if tpe_check.isin([user]).any().any() == True:
                user_table.loc[user_table[user_table['Username'] == user].index.values, file.split('.')[0]] = round(float(tpe_check.loc[tpe_check['Username'] == user]['TPE'].values[0]))
            elif tpe_check.isin([user]).any().any() == False:
                user_table.loc[user_table[user_table['Username'] == user].index.values, file.split('.')[0]] = 0

# Check all defined weeks of Activity Check threads and award TPE.
def ActivityChecks(x, AC_list):
    ac_check = pd.read_csv(r'C:\Users\GenworthOEM\PycharmProjects\TPEScout\acthreads.txt', sep=',', names=['ACNum','ThreadID'])
    for check in AC_list:
        search_URL = 'https://forums.sim-football.com/misc.php?action=whoposted&tid=' + str(ac_check[ac_check['ACNum'] == check].iloc[0,1])
        page = requests.get(search_URL)
        ac_thread = pd.read_html(str(BeautifulSoup(page.text, features='lxml').find('table', attrs={'class': 'tborder'})))[0]
        for user in x:
            if ac_thread.iloc[:,0].str.contains(user).any() == True:
                user_table.loc[user_table[user_table['Username'] == user].index.values, str('AC' + str(check))] = 2
            elif ac_thread.iloc[:,0].str.contains(user).any() == False:
                user_table.loc[user_table[user_table['Username'] == user].index.values, str('AC' + str(check))] = 0
        # Site only allows for searching every ten seconds.
        time.sleep(10)

# Check all potential locations for Weekly Training and award TPE.
def WeeklyTraining(x, AC_list):
    wt_threads = pd.read_csv(r'C:\Users\GenworthOEM\PycharmProjects\TPEScout\training_threads.txt', names=['ThreadID'])
    total_training = pd.DataFrame()
    for team in wt_threads['ThreadID']:
        search_URL = 'https://forums.sim-football.com/showthread.php?mode=threaded&tid=' + str(team)
        page = requests.get(search_URL)
        train_thread = list(pd.read_html(str(BeautifulSoup(page.text, features='lxml').find_all('table', attrs={'class': 'tborder'})[1]))[0].iloc[1])[0]
        train_thread = pd.DataFrame(re.split(r',', train_thread),columns=['User']).iloc[1:,]
        train_thread.drop(train_thread.tail(1).index, inplace = True)
        train_thread['User'] = train_thread['User'].str.split('- by').str[1]
        train_thread = train_thread['User'].str.split(' - ', expand=True)
        train_thread.columns = ['User', 'Timestamp']
        # Convert common language 'yesterday', 'today', etc. to usable timestamp data.
        if train_thread['Timestamp'].str.contains('Yesterday').any() == True:
            train_thread.loc[train_thread['Timestamp'].str.contains('Yesterday', na = False), 'Timestamp'] = pd.Timestamp.now() - pd.Timedelta(days=1)
        if train_thread['Timestamp'].str.contains('Today').any() == True:
            train_thread.loc[train_thread['Timestamp'].str.contains('Today', na = False), 'Timestamp'] = pd.Timestamp.now()
        if train_thread['Timestamp'].str.contains('minute').any() == True:
            train_thread.loc[train_thread['Timestamp'].str.contains('minute', na = False), 'Timestamp'] = pd.Timestamp.now()
        if train_thread['Timestamp'].str.contains('hour').any() == True:
            train_thread.loc[train_thread['Timestamp'].str.contains('hour', na = False), 'Timestamp'] = pd.Timestamp.now()
        train_thread['Timestamp'] = pd.to_datetime(train_thread['Timestamp'], errors='coerce')
        total_training = total_training.append(train_thread, ignore_index=True)
        # Site only allows for searching every ten seconds.
        time.sleep(10)
    for user in x:
        for check in AC_list:
            date_offset = current_AC - check
            monday = pd.to_datetime(pd.Timestamp.date(today - pd.Timedelta(days=pd.Timestamp.weekday(today)) - pd.Timedelta(days=date_offset * 7)))
            sunday = pd.to_datetime(pd.Timestamp.date(today - pd.Timedelta(days=pd.Timestamp.weekday(today)) - pd.Timedelta(days=date_offset * 7 - 7)))
            mask = (total_training['Timestamp'] >= monday) & (total_training['Timestamp'] < sunday) & (total_training['User'].str.strip() == user)
            if pd.Series(mask).any() == True:
                user_table.loc[user_table[user_table['Username'] == user].index.values, str('WT' + str(check))] = 5
            elif pd.Series(mask).any() == False:
                user_table.loc[user_table[user_table['Username'] == user].index.values, str('WT' + str(check))] = 0


def Rookie(x):
    search_URL = 'https://forums.sim-football.com/showthread.php?mode=threaded&tid=12151'
    page = requests.get(search_URL)
    rook_thread = list(pd.read_html(str(BeautifulSoup(page.text, features='lxml').find_all('table', attrs={'class': 'tborder'})[1]))[0].iloc[1])[0]
    rook_thread = pd.DataFrame(re.split(r'Rookie Point Task - by ', rook_thread),columns=['User']).iloc[1:,]
    rook_thread = rook_thread['User'].str.split(' - ', expand=True).iloc[:,0:2]
    rook_thread.columns = ['User','Timestamp']
    rook_thread['Timestamp'] = rook_thread['Timestamp'].str.split(' AM| PM').str[0]
    # Convert common language 'yesterday', 'today', etc. to usable timestamp data.
    if rook_thread['Timestamp'].str.contains('Yesterday').any() == True:
        rook_thread.loc[rook_thread['Timestamp'].str.contains('Yesterday', na = False), 'Timestamp'] = pd.Timestamp.now() - pd.Timedelta(days=1)
    if rook_thread['Timestamp'].str.contains('Today').any() == True:
        rook_thread.loc[rook_thread['Timestamp'].str.contains('Today', na = False), 'Timestamp'] = pd.Timestamp.now()
    if rook_thread['Timestamp'].str.contains('minute').any() == True:
        rook_thread.loc[rook_thread['Timestamp'].str.contains('minute', na = False), 'Timestamp'] = pd.Timestamp.now()
    if rook_thread['Timestamp'].str.contains('hour').any() == True:
        rook_thread.loc[rook_thread['Timestamp'].str.contains('hour', na = False), 'Timestamp'] = pd.Timestamp.now()
    rook_thread['Timestamp'] = pd.to_datetime(rook_thread['Timestamp'], errors='coerce')
    for user in x:
        if rook_thread.loc[rook_thread['User'].str.contains(user), 'Timestamp'].max() > today - pd.Timedelta(weeks=8):
            user_table.loc[user_table[user_table['Username'] == user].index.values, str('Rookie Tasks')] = 12
        else:
            user_table.loc[user_table[user_table['Username'] == user].index.values, str('Rookie Tasks')] = 0
    # Site only allows for searching every ten seconds.
    time.sleep(10)

def Wiki(x):
    search_URL = 'https://forums.sim-football.com/showthread.php?mode=threaded&tid=9492'
    page = requests.get(search_URL)
    wiki_thread = list(pd.read_html(str(BeautifulSoup(page.text, features='lxml').find_all('table', attrs={'class': 'tborder'})[1]))[0].iloc[1])[0]
    wiki_thread = pd.DataFrame(re.split(r' Wiki ', wiki_thread),columns=['User']).iloc[2:,]
    wiki_thread['User'] = wiki_thread['User'].str.split('- by ').str[1]
    wiki_thread['User'] = wiki_thread['User'].str.split(',').str[0]
    wiki_thread['User'] = wiki_thread['User'].str.split('ago').str[0]
    wiki_thread[['User', 'Timestamp']] = wiki_thread['User'].str.split(' - ', expand = True)
    # Convert common language 'yesterday', 'today', etc. to usable timestamp data.
    if wiki_thread['Timestamp'].str.contains('Yesterday').any() == True:
        wiki_thread.loc[wiki_thread['Timestamp'].str.contains('Yesterday', na = False), 'Timestamp'] = pd.Timestamp.now() - pd.Timedelta(days=1)
    if wiki_thread['Timestamp'].str.contains('Today').any() == True:
        wiki_thread.loc[wiki_thread['Timestamp'].str.contains('Today', na = False), 'Timestamp'] = pd.Timestamp.now()
    if wiki_thread['Timestamp'].str.contains('minute').any() == True:
        wiki_thread.loc[wiki_thread['Timestamp'].str.contains('minute', na = False), 'Timestamp'] = pd.Timestamp.now()
    if wiki_thread['Timestamp'].str.contains('hour').any() == True:
        wiki_thread.loc[wiki_thread['Timestamp'].str.contains('hour', na = False), 'Timestamp'] = pd.Timestamp.now()
    wiki_thread['Timestamp'] = pd.to_datetime(wiki_thread['Timestamp'], errors='coerce')
    for user in x:
        if wiki_thread.loc[wiki_thread['User'].str.contains(user), 'Timestamp'].max() > today - pd.Timedelta(weeks=8):
            user_table.loc[user_table[user_table['Username'] == user].index.values, str('Wiki')] = 10
        else:
            user_table.loc[user_table[user_table['Username'] == user].index.values, str('Wiki')] = 0
    # Site only allows for searching every ten seconds.
    time.sleep(10)

ActivityChecks(users, AC_list)
ClaimThread(users)
Wiki(users)
Rookie(users)
WeeklyTraining(users, AC_list)
user_table.to_csv(r'C:\Users\GenworthOEM\PycharmProjects\TPEScout\output\output.csv', index = False)