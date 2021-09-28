#in-app imports
from knowledge_maps.models import KnowledgeMapModel
from link_clicks.models import LinkClickModel
from goals.models import GoalModel

#external imports
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def create_table():

    # clicks : url,user_id,click_time
    # goals :user_id,goal_concepts,last_updated

    goals = GoalModel.objects.all().order_by('last_updated')

    intervals = []
    set_goal = []

    for goal in goals:
    # finding the time intevel between goal and the time click

        intervals.append (
                        find_intervel (goal.last_updated,LinkClickModel)
                         )

        set_goal.append(goal.last_updated.month)

    # seaborn syncs best with Pandas this is why we would like to consolidate the lists into one data frame

    df = pd.DataFrame({'Intervals': intervals,'Month setting goal': set_goal})

    plot_interval(df)


def find_intervel(set_goal,linkClickModel):
    # gets the date of goal setting (last_updated)

    window = set_goal - timedelta(hours=1)
    # search all the records from click_time that have the same day

    clicks = linkClickModel.objects.all().filter(click_time__range=(window,set_goal)).order_by('-click_time')

    # if there is an interval within the time window interval will calculate otherwise the interval will be 0
    if len(clicks) > 0:
        smallest = clicks[0].click_time
    else :
        smallest = set_goal

    interval = (set_goal - smallest).total_seconds()

    return interval


def plot_interval(df, plt=plt):

    path = 'volume/'
    file_name = 'intervel_plot'

    # 0 Value mean that no interval is found in the window we set for it so we drop all 0 values
    non_zero_df = df[df['Intervals'] > 0]

    drop_percentage = (len(df)-len(non_zero_df) )/len(df) * 100
    print(f'{np.round(drop_percentage,2)}% of users did not stand in the time window and dropped from the plot')

    plt.figure(figsize=(15, 9))

    # sets the Y axis to 12 months
    plt.ylim(1,12)

    plt.title('Set goal / Link Click intervals distribution over months')
    sns.scatterplot(x='Intervals', y='Month setting goal', data=non_zero_df)
    plt.savefig(f'{path}{file_name}.png')

    # checks if the file exists

    if os.path.isfile(f'{path}{file_name}.png'):
        print(f'The plot is saved at {path}{file_name}.png')
    else:
        print('File is not saved')

create_table()


