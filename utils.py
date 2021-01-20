import csv
import random
import pickle


def read_csv(path):
    questions = []
    with open(path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            questions.append(row['question'])
    return questions


def get_random_question(questions):
    return random.choice(questions)


def get_pickle_file(path):
    with open(path, 'rb') as file:
        pickle_file = pickle.load(file)
    return pickle_file

