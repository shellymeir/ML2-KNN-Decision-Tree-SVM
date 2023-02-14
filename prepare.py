# -*- coding: utf-8 -*-
"""prepare.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1w9DJxmeVBZR-IspNE2ITGrKlXgQLQBal
"""

import copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
import math
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler

def blood_type_to_ohe(data):
  data = pd.get_dummies(data, columns=['blood_type'])
  return data

def extract_features_from_symptoms(data):
  for idx in range(len(data['symptoms'])):
   if isinstance(data['symptoms'].iloc[idx], str):
     data['symptoms'].iloc[idx] = data['symptoms'].iloc[idx].split(';')

  to_concat = data['symptoms'].str.join('|').str.get_dummies()
  data = pd.concat([data, to_concat], axis=1)
  del data['symptoms']
  return data

def sex_to_ohe(data):
  return pd.get_dummies(data, columns=['sex'])

def craft_employed_feature(data):
  employed = [None]*(len(data['job']))

  for idx in range(len(data['job'])):
    if pd.isna(data['job'].iloc[idx]):
      employed[idx] = 0 
    else:
      employed[idx] = 1
  data['employed'] = employed
  del data['job']

  return data

def craft_x_y_coordinates_features(data):
  xs = []
  ys = []

  for idx in range(len(data['current_location'])):
    if isinstance(data['current_location'].iloc[idx], str):
      coordinates = data['current_location'].iloc[idx].split(',')
      xs.append(float(coordinates[0][2:-1])) 
      ys.append(float(coordinates[1][2:-2]))
    else:
      xs.append(float('NaN')) 
      ys.append(float('NaN'))
      
  del data['current_location']
  data['current_location_x_coordinate'] = xs
  data['current_location_y_coordinate'] = ys

  return data

def craft_state_feature(data):
  states = []
  for idx in range(len(data['address'])):
    if isinstance(data['address'].iloc[idx], str):
      add = data['address'].iloc[idx].split(',')
      state = add[-1].split(' ')[1]
    else:
      state = float('NaN')
    states.append(state)

  data['state'] = states
  del data['address']

  return data

def craft_days_since_pcr_feature(data):
  all_dates = []
  pcr_dates = copy.deepcopy(data['pcr_date'])

  for idx in range(len(data['pcr_date'])):
    if isinstance(data['pcr_date'].iloc[idx], str):
      data['pcr_date'].iloc[idx] = data['pcr_date'].iloc[idx][0:4:] + data['pcr_date'].iloc[idx][5::]
      data['pcr_date'].iloc[idx] = data['pcr_date'].iloc[idx][0:6:] + data['pcr_date'].iloc[idx][7::]
      data['pcr_date'].iloc[idx] = float(data['pcr_date'].iloc[idx])
      all_dates.append(data['pcr_date'].iloc[idx])

      
  last_date = max(all_dates)
  last_date_list = [last_date//10000, (last_date%10000)//100, last_date%100]
  last_date_in_days = last_date_list[0]*365 + last_date_list[1]*30 + last_date_list[2]

  for idx in range(0,len(pcr_dates)):
    if isinstance(pcr_dates.iloc[idx], str):
      date = pcr_dates.iloc[idx].split('-')
      for i in range(len(date)):
        date[i] = float(date[i])
      pcr_dates.iloc[idx] = date

  for i in range(len(pcr_dates)):
    if isinstance(pcr_dates.iloc[i], list):
      pcr_dates.iloc[i] = pcr_dates.iloc[i][0]*365 + pcr_dates.iloc[i][1]*30 + pcr_dates.iloc[i][2]
      pcr_dates.iloc[i] = last_date_in_days - pcr_dates.iloc[i]

  data['days_since_pcr'] = pcr_dates
  del data['pcr_date']

  return data

def clean_outliers_IQR(data):
  features_to_clean = ['current_location_x_coordinate','current_location_y_coordinate', 'days_since_pcr' , 'num_of_siblings', 'household_income',
                     'conversations_per_day', 'happiness_score', 'sport_activity', 'age',
                     'PCR_01', 'PCR_02', 'PCR_03', 'PCR_04', 'PCR_05', 'PCR_06', 'PCR_07', 'PCR_08', 'PCR_09', 'PCR_10']
  
  for feature in features_to_clean:
    Q1 = data[feature].quantile(0.25)
    Q3 = data[feature].quantile(0.75)
    IQR = Q3 - Q1
    mean = data[feature].mean()
    for idx in range(len(data[feature])):
      if (data[feature].iloc[idx] < (Q1 - 1.5 * IQR)) or (data[feature].iloc[idx] > (Q3 + 1.5 * IQR)):
        data[feature].iloc[idx] = mean
        if feature == 'age':
          data[feature].iloc[idx] = Q3 + 1.5*IQR
  return data

def calculate_weight_IQR_limits_by_age(train, age):
    weights=[]
    for idx in range(len(train['age'])):
      if not(math.isnan(train['age'].iloc[idx])) and not(math.isnan(train['weight'].iloc[idx])):
        if train['age'].iloc[idx]<50:
          diff = 0
        else:
          diff = 11
        if abs((train['age'].iloc[idx]) - age) <= diff :
            weights.append(train['weight'].iloc[idx])
    if weights == []:
      general_mean = train['weight'].mean()
      return general_mean, general_mean, general_mean
    weights_df = pd.DataFrame(weights)
    Q1 = weights_df[0].quantile(0.25)
    Q3 = weights_df[0].quantile(0.75)
    Q2 = weights_df[0].quantile(0.5)
    IQR = Q3 - Q1
    return Q1 - 1.5 * IQR, Q3 + 1.5 * IQR, Q2

def clean_weight_outliers_by_age(train, test):
  array_of_low_limit_high_limit_Q2_from_age_1_to_60 = []
  for i in range(0,61):
    array_of_low_limit_high_limit_Q2_from_age_1_to_60.append([0.0,0.0,0.0])
  for age in range(0,61):
    array_of_low_limit_high_limit_Q2_from_age_1_to_60[age] = calculate_weight_IQR_limits_by_age(train, age)
  mean_general = train['weight'].mean()
  upper_general_limit =  train['weight'].quantile(0.75) + 1.5*(train['weight'].quantile(0.75)-train['weight'].quantile(0.25))
  for idx in range(len(train['patient_id'])):
    if not math.isnan(train['weight'].iloc[idx]):
      if not(math.isnan(train['age'].iloc[idx])): #if age exist
        if  60 < train['age'].iloc[idx]:
          train['weight'].iloc[idx] = mean_general
        low_limit, high_limit, Q2 = array_of_low_limit_high_limit_Q2_from_age_1_to_60[int(train['age'].iloc[idx])]
        if  high_limit < train['weight'].iloc[idx]:
          train['weight'].iloc[idx] = Q2
      else:
        if upper_general_limit<train['weight'].iloc[idx]:
          train['weight'].iloc[idx] = mean_general
  for idx in range(len(test['patient_id'])):
    if not math.isnan(test['weight'].iloc[idx]):
      if not(math.isnan(test['age'].iloc[idx])): #if age exist
        if  60 < test['age'].iloc[idx]:
          test['weight'].iloc[idx] = mean_general
        low_limit, high_limit, Q2 = array_of_low_limit_high_limit_Q2_from_age_1_to_60[int(test['age'].iloc[idx])]
        if  high_limit < test['weight'].iloc[idx]:
          test['weight'].iloc[idx] = Q2
      else:
        if upper_general_limit<test['weight'].iloc[idx]:
          test['weight'].iloc[idx] = mean_general
  
  return test, train

def calculate_sugar_levels_IQR_limits_by_weight(train, weight):
  sugar_levels_list=[]
  for idx in range(len(train['sugar_levels'])):
    if not(math.isnan(train['sugar_levels'].iloc[idx])) and not(math.isnan(train['weight'].iloc[idx])):
      if train['weight'].iloc[idx] <= 100 and 5 <= train['weight'].iloc[idx]:
        diff = 5
      else:
        diff = 20
      if abs((train['weight'].iloc[idx]) - weight) <= diff :
        sugar_levels_list.append(train['sugar_levels'].iloc[idx])
  if sugar_levels_list == []:
    general_mean = train['sugar_levels'].mean()
    return general_mean, general_mean, general_mean
  sugar_levels_df = pd.DataFrame(sugar_levels_list)
  Q1 = sugar_levels_df[0].quantile(0.25)
  Q3 = sugar_levels_df[0].quantile(0.75)
  Q2 = sugar_levels_df[0].quantile(0.5)
  IQR = Q3 - Q1
  return Q1 - 1.5 * IQR, Q3 + 1.5 * IQR, Q2

def clean_sugar_levels_outliers_by_weight(train, test):
  array_of_low_limit_high_limit_Q2_from_weight_1_to_140 = []
  for i in range(1,142):
    array_of_low_limit_high_limit_Q2_from_weight_1_to_140.append([0.0,0.0,0.0])
  for weight in range(1,141):
    array_of_low_limit_high_limit_Q2_from_weight_1_to_140[weight] = calculate_sugar_levels_IQR_limits_by_weight(train, weight)
  mean_general = train['sugar_levels'].mean()
  upper_general_limit =  train['sugar_levels'].quantile(0.75) + 1.5*(train['sugar_levels'].quantile(0.75)-train['sugar_levels'].quantile(0.25))
  for idx in range(len(train['patient_id'])):
    if not math.isnan(train['sugar_levels'].iloc[idx]):
      if not(math.isnan(train['weight'].iloc[idx])): #if weight exist
        if 140 < train['weight'].iloc[idx]:
          train['sugar_levels'].iloc[idx] = mean_general
        low_limit, high_limit, Q2 = array_of_low_limit_high_limit_Q2_from_weight_1_to_140[int(train['weight'].iloc[idx])]
        if  high_limit < train['sugar_levels'].iloc[idx]:
          train['sugar_levels'].iloc[idx] = Q2
      else:
        if upper_general_limit<train['sugar_levels'].iloc[idx]:
          train['sugar_levels'].iloc[idx] = mean_general

  for idx in range(len(test['patient_id'])):
    if not math.isnan(test['sugar_levels'].iloc[idx]):
      if not(math.isnan(test['weight'].iloc[idx])): #if weight exist
        if 140 < test['weight'].iloc[idx]:
          test['sugar_levels'].iloc[idx] = mean_general
        low_limit, high_limit, Q2 = array_of_low_limit_high_limit_Q2_from_weight_1_to_140[int(test['weight'].iloc[idx])]
        if  high_limit < test['sugar_levels'].iloc[idx]:
          test['sugar_levels'].iloc[idx] = Q2
      else:
        if upper_general_limit<test['sugar_levels'].iloc[idx]:
          test['sugar_levels'].iloc[idx] = mean_general
  
  return test, train

def clean_outliers_from_pcr_tests(data):
  PCR_TESTS = ['PCR_01', 'PCR_02', 'PCR_03', 'PCR_04', 'PCR_05', 'PCR_06', 'PCR_07', 'PCR_08', 'PCR_09', 'PCR_10']

  for pcr_test in PCR_TESTS:
    for patient in range(len(data[pcr_test])):
      if data['days_since_pcr'].iloc[patient] >= 389 and data['days_since_pcr'].iloc[patient] <= 407:
        data[pcr_test].iloc[patient] = float('NaN')
  return data

def fill_missing_data_with_mean(train, test):
  features_to_impute = ['current_location_x_coordinate','current_location_y_coordinate', 'days_since_pcr' , 'num_of_siblings', 'household_income',
                        'conversations_per_day', 'happiness_score', 'sport_activity',
                        'PCR_01', 'PCR_02', 'PCR_03', 'PCR_04', 'PCR_05', 'PCR_06', 'PCR_07', 'PCR_08', 'PCR_09', 'PCR_10']
  for feature in features_to_impute:
      mean = train[feature].mean()
      for idx in range(len(train[feature])):
        if math.isnan(train[feature].iloc[idx]):
          train[feature].iloc[idx] = mean
      for idx in range(len(test[feature])):
        if math.isnan(test[feature].iloc[idx]):
          test[feature].iloc[idx] = mean
  return test, train

def calculate_average_weight_by_sex_and_age(sex, age, train):
  sum_of_weights = 0
  num_of_weights = 0
  for idx in range(len(train[sex])):
    if not (math.isnan(train[sex].iloc[idx])) and not(math.isnan(train['age'].iloc[idx])) and not(math.isnan(train['weight'].iloc[idx])):
      if train[sex].iloc[idx] == 1 and abs((train['age'].iloc[idx]) - age) <= 2 :
            sum_of_weights+=train['weight'].iloc[idx]
            num_of_weights+=1
  if num_of_weights != 0:
    return sum_of_weights/num_of_weights
  return 0

def choose_M_or_F_by_weight_and_age(weight, age, train):
  female_average_in_this_age = calculate_average_weight_by_sex_and_age('sex_F', age, train)
  male_average_in_this_age = calculate_average_weight_by_sex_and_age('sex_M', age, train)
  diff_from_female = abs(female_average_in_this_age - weight)
  diff_from_male = abs(male_average_in_this_age - weight)
  if diff_from_female < diff_from_male:
    return 'sex_F'
  else:
    return 'sex_M'

def get_55_percents_female():
  return np.random.choice(['sex_F', 'sex_M'], p=[0.55, 0.45])

def fill_missing_sex_by_weight(train, test):
  for idx in range(len(train['patient_id'])):
    if train['sex_F'].iloc[idx] == 0 and train['sex_M'].iloc[idx] == 0:
      if not(math.isnan(train['age'].iloc[idx])) and not(math.isnan(train['weight'].iloc[idx])):
        M_or_F = choose_M_or_F_by_weight_and_age(train['weight'].iloc[idx], train['age'].iloc[idx], train)
        train[M_or_F].iloc[idx] = 1
      else:
        train[get_55_percents_female()].iloc[idx] = 1

  for idx in range(len(test['patient_id'])):
    if test['sex_F'].iloc[idx] == 0 and test['sex_M'].iloc[idx] == 0:
      if not(math.isnan(test['age'].iloc[idx])) and not(math.isnan(test['weight'].iloc[idx])):
        M_or_F = choose_M_or_F_by_weight_and_age(test['weight'].iloc[idx], test['age'].iloc[idx], train)
        test[M_or_F].iloc[idx] = 1
      else:
        test[get_55_percents_female()].iloc[idx] = 1
        
  return test, train

def fill_missing_weight_by_age(train, test):
  for idx in range(len(train['patient_id'])):
    if math.isnan(train['weight'].iloc[idx]):
      sex = 'sex_F'
      if train['sex_M'].iloc[idx] == 1:
        sex = 'sex_M'
      if  not(math.isnan(train['age'].iloc[idx])):
        train['weight'].iloc[idx] = calculate_average_weight_by_sex_and_age(sex, train['age'].iloc[idx], train)
      else:
        train['weight'].iloc[idx] = train['weight'].mean()

  for idx in range(len(test['patient_id'])):
    if math.isnan(test['weight'].iloc[idx]):
      sex = 'sex_F'
      if test['sex_M'].iloc[idx] == 1:
        sex = 'sex_M'
      if not(math.isnan(test['age'].iloc[idx])):
        test['weight'].iloc[idx] = calculate_average_weight_by_sex_and_age(sex, test['age'].iloc[idx], train)
      else:
        test['weight'].iloc[idx] = train['weight'].mean()

  return test, train

def fill_missing_sugar_levels_by_weight(train, test):
  for idx in range(len(train['patient_id'])):
    if math.isnan(train['sugar_levels'].iloc[idx]):
      x,y,Q2 = calculate_sugar_levels_IQR_limits_by_weight(train, train['weight'].iloc[idx])
      train['sugar_levels'].iloc[idx] = Q2
  
  for idx in range(len(test['patient_id'])):
    if math.isnan(test['sugar_levels'].iloc[idx]):
      x,y,Q2 = calculate_sugar_levels_IQR_limits_by_weight(train, test['weight'].iloc[idx])
      test['sugar_levels'].iloc[idx] = Q2

  return test, train

def calculate_average_age_by_weight(train, weight):
  list_of_ages = []
  for idx in range(len(train['patient_id'])):
    if  not(math.isnan(train['age'].iloc[idx])) and not(math.isnan(train['weight'].iloc[idx])):
      if abs((train['weight'].iloc[idx]) - weight) <= 5 :
            list_of_ages.append(train['age'].iloc[idx])
  if list_of_ages == []:
    return train['age'].mean()
  return sum(list_of_ages) / len(list_of_ages)

def fill_missing_age_by_weight(train, test):
  for idx in range(len(train['patient_id'])):
    if math.isnan(train['age'].iloc[idx]):
      train['age'].iloc[idx] = calculate_average_age_by_weight(train, train['weight'].iloc[idx])
  
  for idx in range(len(test['patient_id'])):
    if math.isnan(test['age'].iloc[idx]):
      test['age'].iloc[idx] = calculate_average_age_by_weight(train, test['weight'].iloc[idx])

  return test, train

def change_data_to_binary(data):
  covid_b = [None]*len(data['patient_id'])
  for idx in range(len(data['covid'])):
    if data['covid'].iloc[idx]:
      covid_b[idx] = float(1)
    else:
      covid_b[idx] = float(-1)
  data['covid'] = covid_b

  risk_b = [None]*len(data['patient_id'])
  for idx in range(len(data['risk'])):
    if data['risk'].iloc[idx] == 'High':
      risk_b[idx] = float(1)
    if data['risk'].iloc[idx] == 'Low':
      risk_b[idx] = float(-1)
  data['risk'] = risk_b

  spread_b = [None]*len(data['patient_id'])
  for idx in range(len(data['spread'])):
    if data['spread'].iloc[idx] == 'High':
      spread_b[idx] = float(1)
    if data['spread'].iloc[idx] == 'Low':
      spread_b[idx] = float(-1)
  data['spread'] = spread_b

  return data

def normalize_data(data):
  
  feature_and_scaler = { 'age': MinMaxScaler(), 'num_of_siblings': MinMaxScaler(), 
                       'household_income': MinMaxScaler(), 'conversations_per_day': StandardScaler(), 
                       'sugar_levels': StandardScaler(), 'PCR_01': StandardScaler(), 'PCR_02': StandardScaler(), 
                       'PCR_03': StandardScaler(), 'PCR_04': StandardScaler(), 'PCR_05': StandardScaler(), 
                       'PCR_07': StandardScaler(), 'PCR_08': StandardScaler(), 'PCR_10': StandardScaler(), 
                       'blood_type_A+': MinMaxScaler(), 'blood_type_A-': MinMaxScaler(), 'blood_type_AB+': MinMaxScaler(), 
                       'blood_type_AB-': MinMaxScaler(), 'blood_type_B+': MinMaxScaler(), 'blood_type_B-': MinMaxScaler(), 
                       'blood_type_O+': MinMaxScaler(), 'blood_type_O-': MinMaxScaler(), 'cough': MinMaxScaler(), 
                       'fever': MinMaxScaler(), 'headache': MinMaxScaler(), 'low_appetite': MinMaxScaler(), 
                       'shortness_of_breath': MinMaxScaler(), 'sex_F': MinMaxScaler(), 'current_location_x_coordinate': MinMaxScaler(), 
                       'current_location_y_coordinate': MinMaxScaler(), 'days_since_pcr': StandardScaler() }

  for feature in feature_and_scaler:
    (feature_and_scaler[feature]).fit(data[[feature]])
    data[feature] = (feature_and_scaler[feature]).transform(data[[feature]])
  
  return data

def prepare_data(data, training_data):
  np.random.seed(8)

  train_copy = copy.deepcopy(training_data)
  data_copy = copy.deepcopy(data)
  
  # transform blood type to ohe
  data_copy = blood_type_to_ohe(data_copy)
  train_copy = blood_type_to_ohe(train_copy)

  # extracting features from symptoms
  data_copy = extract_features_from_symptoms(data_copy)
  train_copy = extract_features_from_symptoms(train_copy)


  # convert sex feature to ohe
  data_copy = sex_to_ohe(data_copy)
  train_copy = sex_to_ohe(train_copy)
  

  # craft new feature 'employed' from job feature
  data_copy = craft_employed_feature(data_copy)
  train_copy = craft_employed_feature(train_copy)


  # craft new features 'x_coordinates' and 'y_coordinates' from 'current_location' feature
  train_copy = craft_x_y_coordinates_features(train_copy)
  data_copy = craft_x_y_coordinates_features(data_copy)


  # craft new feature 'state' from 'address' feature
  data_copy = craft_state_feature(data_copy)
  train_copy = craft_state_feature(train_copy)


  # craft new feature 'days_since_pcr' from 'pcr_date' feature
  data_copy = craft_days_since_pcr_feature(data_copy)
  train_copy = craft_days_since_pcr_feature(train_copy)
    
  # cleaning outliers from pcr tests
  data_copy = clean_outliers_from_pcr_tests(data_copy)
  train_copy = clean_outliers_from_pcr_tests(train_copy)


  # cleaning outliers by IQR based technique
  data_copy = clean_outliers_IQR(data_copy)
  train_copy = clean_outliers_IQR(train_copy)


  # clean weight feature by age feature (of the training data!)
  data_copy, train_copy = clean_weight_outliers_by_age(train_copy, data_copy)


  # clean sugar_levels feature by weight feature (of the training data!)
  data_copy, train_copy = clean_sugar_levels_outliers_by_weight(train_copy, data_copy)





  # fill missing num_of_siblings in test according to train median
  median = train_copy.num_of_siblings.median()
  data_copy['num_of_siblings'] = data_copy.num_of_siblings.fillna(data_copy.num_of_siblings.median())
  train_copy['num_of_siblings'] = train_copy.num_of_siblings.fillna(train_copy.num_of_siblings.median())


  # fill missing data of some features in test with means of same features in train
  data_copy, train_copy = fill_missing_data_with_mean(train_copy, data_copy)


  # fill missing sex with weight
  data_copy, train_copy = fill_missing_sex_by_weight(train_copy, data_copy)


  # fill missing weight by age and sex
  data_copy, train_copy = fill_missing_weight_by_age(train_copy, data_copy)


  # fill missing sugar_levels by weight
  data_copy, train_copy = fill_missing_sugar_levels_by_weight(train_copy, data_copy)


  # fill missing age by weight
  data_copy, train_copy = fill_missing_age_by_weight(train_copy, data_copy)


  # change data to -1,1
  data_copy = change_data_to_binary(data_copy)

  del data_copy['weight']
  del data_copy['sex_M']
  del data_copy['PCR_06']
  del data_copy['PCR_09']
  del data_copy['happiness_score']
  del data_copy['sport_activity']
  del data_copy['employed']
  del data_copy['state']


  # normalize data
  data_copy = normalize_data(data)


  return data_copy