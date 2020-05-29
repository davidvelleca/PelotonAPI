import pandas as pd
import requests
import json
from pandas.io.json import json_normalize
from functools import reduce

#Some inputs for the User - could be changed from prompts to hard coded values
user = input('Enter your username or email: ')
pw = input('Enter your password: ')
excel = input('Specify Excel filename & location (include ".xlsx"): ')

#Authenticate the user
s = requests.Session()
payload = {'username_or_email': user, 'password':pw}
s.post('https://api.onepeloton.com/auth/login', json=payload)

'''First API Call - GET User ID for all other Calls'''
#Get User ID to pass into other calls
me_url = 'https://api.onepeloton.com/api/me'
response = s.get(me_url)
apidata = s.get(me_url).json()

#Flatten API response into a temporary dataframe
df_my_id = json_normalize(apidata, 'id', ['id'])
df_my_id_clean = df_my_id.iloc[0]
my_id = (df_my_id_clean.drop([0])).values.tolist()

'''Second API Call - GET Workout, Ride & Instructor Details''' 
#API URL - 
url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=250&page=0'.format(*my_id)
response = s.get(url)
data = s.get(url).json()

#Flatten API response into a temporary dataframe
df_workouts_raw = json_normalize(data['data'])

#Keep only necessary columns as a new pandas dataframe - this list can be modified based on the user's 
#preference.  Right now, primarily excluding duplicated columns, excess ID columns, and social media
#columns for the Instructors
df_workouts = df_workouts_raw.drop(df_workouts_raw.columns[[4, 5, 11, 13, 
15, 16, 17, 20, 24, 25, 27, 28, 29, 31, 32, 33, 35, 37, 39, 40, 41, 42, 
43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 59, 60, 63, 
64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 82, 
83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 96, 97, 98, 99, 100, 103, 
105, 106, 107, 108]], axis = 1)

#Print Message Workout Data Complete
print('Workout Data processing complete')

'''Third API Call - GET Workout Metrics''' 
#Create Dataframe of Workout IDs to run through our Loop
df_workout_ids = df_workouts.filter(['id'], axis=1)

#Define the imputs for the for loop
workout_ids = df_workout_ids.values.tolist()
workout_ids2 = [i[0] for i in workout_ids]

#Create empty dataframes to write iterations to
df_tot_metrics = pd.DataFrame([])
df_avg_metrics = pd.DataFrame([])

for workout_id in workout_ids2:
     response2 = s.get('https://api.onepeloton.com/api/workout/{}/performance_graph?every_n=300'.format(workout_id))
     data2 = response2.json()
     #Flatten API response into a temporary dataframe - exception handling because each workout type has a 
     #different structure to the API response, with different metrics.  Additionally, this call also generates
     #a number of rows so we have to transpose and flatten the dataframe.
     try:
          df_avg_raw = json_normalize(data2['average_summaries'])
     except:
          pass
     else:
          df_avg_raw = json_normalize(data2['average_summaries'])
          df_avg_stg = df_avg_raw.T
     try:
          df_avg_stg.columns = df_avg_stg.iloc[0]
     except:
          pass
     else:
          df_avg_stg.columns = df_avg_stg.iloc[0]
          df_avg = df_avg_stg.drop(['display_name', 'slug', 'display_unit'])
          df_avg['id'] = workout_id
     try:
          df_tot_raw = json_normalize(data2['summaries'])
     except:
          pass
     else:
          df_tot_raw = json_normalize(data2['summaries'])
          df_tot_stg = df_tot_raw.T
     try:
          df_tot_stg.columns = df_tot_stg.iloc[0]
     except:
          pass
     else:
          df_tot_stg.columns = df_tot_stg.iloc[0]
          df_tot = df_tot_stg.drop(['display_name', 'slug', 'display_unit'])
          df_tot['id'] = workout_id
     #Append each run through the loop to the dataframe
     df_tot_metrics = df_tot_metrics.append(df_tot, sort=False)
     try:
          df_avg_metrics = df_avg_metrics.append(df_avg, sort=False)
     except:
          pass
     else:
          df_avg_metrics = df_avg_metrics.append(df_avg, sort=False)

df_tot_metrics_clean = df_tot_metrics.drop_duplicates()
df_avg_metrics_clean = df_avg_metrics.drop_duplicates()
df_workout_metrics = df_avg_metrics_clean.merge(df_tot_metrics_clean, left_on='id', right_on='id', how='right')

#Print Message Workout Metrics Complete
print('Workout Metrics processing complete')

'''Fourth API Call - GET Workout Achievements''' 
df_workout_achievements = pd.DataFrame([])

for workout_id in workout_ids2:
     response = s.get('https://api.pelotoncycle.com/api/workout/{}/achievements'.format(workout_id))
     data3 = response.json()
     #Flatten API response into a temporary dataframe
     df_workout_achievements_stg = json_normalize(data3['data'])
     df_workout_achievements = df_workout_achievements.append(df_workout_achievements_stg, sort=False, ignore_index=True)

df_achievements = df_workout_achievements.drop(['id', 'template.id', 'template.slug', 'template_id', 'user_id'], axis=1)

#Work to put all achievements for a workout on one row - I've chosen to break out to 4 achievements on a workout.  Could possibly 
#be more.  Would need to account for this if so.
#First Step - create a counter by Workout ID
df_achievements['counter'] = df_achievements.sort_values(['workout_id'], ascending=[1]).groupby('workout_id').cumcount() + 1
#Second Step - Break into separate series based on the counter
df_achievements_1 = df_achievements.loc[df_achievements['counter'] == 1]
df_achievements_2 = df_achievements.loc[df_achievements['counter'] == 2]
df_achievements_3 = df_achievements.loc[df_achievements['counter'] == 3]
df_achievements_4 = df_achievements.loc[df_achievements['counter'] == 4]
#Third Step - Rename columns
df_achievements_1.columns = ['template.description_a','template.image_url_a','template.name_a','workout_id','counter_a']
df_achievements_2.columns = ['template.description_b','template.image_url_b','template.name_b','workout_id','counter_b']
df_achievements_3.columns = ['template.description_c','template.image_url_c','template.name_c','workout_id','counter_c']
df_achievements_4.columns = ['template.description_d','template.image_url_d','template.name_d','workout_id','counter_d']
#Fourth Step - Convert series to dataframes
df_achievements_a = pd.DataFrame(df_achievements_1)
df_achievements_b = pd.DataFrame(df_achievements_2)
df_achievements_c = pd.DataFrame(df_achievements_3)
df_achievements_d = pd.DataFrame(df_achievements_4)
#Final Step - Merge the four dataframes into a dataframe with a single row per workout_id
df_achievements_final = reduce(lambda x,y: pd.merge(x,y, on='workout_id', how='outer'), [df_achievements_a, df_achievements_b, df_achievements_c, df_achievements_d])
cols = [c for c in df_achievements_final.columns if c.lower()[:7] != 'counter']
df_achievements_final = df_achievements_final[cols]

#Print Message Workout Achievements Complete
print('Workout Achievements processing complete')

#Left outer join of the Workout Data and Metrics
df_peloton_final_stg = df_workouts.merge(df_workout_metrics, left_on='id', right_on='id', how='left')
df_peloton_final = df_peloton_final_stg.merge(df_achievements_final, left_on='id', right_on='workout_id', how='left')

#Export the merged dataframes to Excel
df_peloton_final.to_excel(excel)

#Success!
print('Full data exported to Excel!')