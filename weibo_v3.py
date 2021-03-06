# -*- coding: utf-8 -*-
import pandas as pd
from pandas import DataFrame, Series
import numpy as np
import sys
import os
import jieba
import math
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import chi2
from sklearn.feature_selection import mutual_info_classif
from sklearn.feature_selection import SelectKBest
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from keras.preprocessing import sequence
from keras.optimizers import SGD, RMSprop, Adagrad
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM


# 加载数据集
'''
每个数据集存在一个path路径下的dataset文件夹下
读取文件csv格式的，丢弃一定的非关键属性进行操作
该函数传递一个path路径，及需要操作的数据集文件
所在的路径。
'''
def loadDataSetSave(path):
    file_name = os.listdir(path + r'\dataset')
    df_data_set = DataFrame()
    for f in file_name:
        file_path = path + r'\dataset' + '\\' + f
        print(file_path)
        data_set = pd.read_csv(file_path, )
        from_which_file = (str(f).split('.'))[0]
        # print(from_which_file)
        data_set['from'] = from_which_file
        df_data_set = pd.concat([df_data_set, data_set])
    df_data_set_droped = df_data_set.drop(['设备源', '微博ID'], axis=1)
    df_data_set_droped.to_csv(path + r'\pre_data_set.csv', encoding='utf-8', index=False)

#处理转发内容
#处理结果为把转发合并至微博内容
def transmitContent(path):
    df_data_set = pd.read_csv(path  + "\\" + "pre_data_set.csv")
    #if_transmit = df_data_set['是否原创']

    #series_transmit = df_data_set['转发内容']
    #series_weibocontent = df_data_set['微博内容']
    #series_new_content = series_weibocontent + series_transmit
    #df_data_set['微博内容'] = series_new_content
    #df_data_set_drop = df_data_set.drop(['转发内容', '是否原创'], axis=1)
    df_data_set.to_csv(path + r'\data_set.csv', encoding='utf-8', index=False)



# 清洗数据
'''
清洗数据，把转发和评论赞，为0的置数字0
在微博内容中，存在着一些NaN值的属性，剔除该值
进行进一步操作
'''
def cleanDateSet(path):
    data_set = pd.read_csv(path + r'\data_set.csv')
    data_set.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)
    # indexs = list(data_set[data_set['微博内容']].index)
    # print(indexs)
    data_set['微博内容'] = data_set['微博内容'].str.strip()
    data_set['转发数'] = data_set['转发数'].str.replace('转发', '0')
    data_set['评论数'] = data_set['评论数'].str.replace('评论', '0')
    data_set['点赞数'] = data_set['点赞数'].str.replace('赞', '0')
    data_set["微博内容"] = data_set["微博内容"].apply(lambda x: np.NaN if str(x) is '' else x)
    clean_data_set = DataFrame(data_set.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False))
    clean_data_set.to_csv(path + r'\clean_data_set.csv', encoding='utf-8', index=False)
    return clean_data_set


# 分词
'''
利用jieba进行分词，并且只保留汉字
'''
def cutWords(path):
    df_data_set = pd.read_csv(path + r'\clean_data_set.csv')
    line = []
    # test_data = [4911, 12152, 12627, 13236]
    # i = 0
    for item in df_data_set['微博内容']:
        temp = ''.join(re.findall(u'[\u4e00-\u9fff]+', item))
        cut_list = jieba.cut(str(temp), cut_all=False)
        line_item = ' '.join(cut_list)
        line.append(line_item)
    df_data_set['微博内容'] = line
    df_data_set["微博内容"] = df_data_set["微博内容"].apply(lambda x: np.NaN if str(x) is '' else x)
    clean_data_set = DataFrame(df_data_set.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False))
    clean_data_set.to_csv(path + r'\cut_data_set.csv', encoding='utf-8', index=False)


# 去除停用词
'''
遗留bug：(已解除)
在某些微博中，最坏的境况，有可能微博内容只有停用词，所以会出现某些微博为空的情况
'''
def drop_stop_words(path):
    df_data_set = pd.read_csv(path + r"\cut_data_set.csv")
    stop_words = [line.strip() for line in open(path + r"\stopwords.txt", 'r', encoding='utf-8')]
    new_word_list = []
    list_df_data_set = list(df_data_set['微博内容'])
    for list_item in list_df_data_set:
        temp_word = ''
        for list_item_word in list_item.split(' '):
            if list_item_word not in stop_words:
                temp_word = temp_word + " " + list_item_word
        new_word_list.append(temp_word)
    df_data_set['微博内容'] = new_word_list
    df_data_set["微博内容"] = df_data_set["微博内容"].apply(lambda x: np.NaN if str(x) is '' else x)
    clean_data_set = DataFrame(df_data_set.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False))
    clean_data_set.to_csv(path + r'\drop_stopword_data_set.csv', encoding='utf-8', index=False)


# 利用关键字来筛选出正负样本
'''
依据每个事件给出具体的关键字，可以抽取出具体的样本数据
'''
def key_word_judgement(path):
    df_data_set = pd.read_csv(path + r"\drop_stopword_data_set.csv")
    weibo_content_list = list(df_data_set['微博内容'])
    i = 0
    flag = []
    for weibo_content in weibo_content_list:
        if weibo_content.find('茂县') != -1 and weibo_content.find('滑坡') != -1:
            flag.append("1")
            i = i + 1
        else:
            flag.append("0") 
    df_data_set['flag'] = flag
    print("corr_number:", end="")
    print(i)
    df_data_set.to_csv(path + r'\key_word_judgement_data_set.csv', encoding='utf-8', index=False)


# 利用多种关键字做测试
def key_word_judgement_using_lay_word(path):
    df_data_set = pd.read_csv(path + r"\drop_stopword_data_set.csv")
    weibo_content_list = list(df_data_set['微博内容'])
    i = 0
    flag = []
    for weibo_content in weibo_content_list:
        if weibo_content.find('北京') != -1 and weibo_content.find('暴雨') != -1:
            flag.append("1")
            i = i + 1
        elif weibo_content.find('北京') != -1 and weibo_content.find('大雨') != -1:
            flag.append("1")
            #print(weibo_content)
            i = i + 1
        else:
            flag.append("0")
    df_data_set['flag'] = flag
    print("new_corr:", end="")
    print(i)
    df_data_set.to_csv(path + r'\key_word_judgement_data_set_using_lay_word.csv', encoding='utf-8', index=False)


# 抽取训练集相关与不相关事件的比例
'''
n_times:表示抽取不相关数据组成集合与相关数据集的比例
n为1：按1:1取样
n为2：按1:2取样
n最多取max_n_times

methon:抽取不相关数据集的方式，具体方式按取值多少来定
methon=1 : 随机取样
methon=2 : 文件分层取样
'''

def get_n_uncorr_set(path, n_times, get_method):
    df_data_set = pd.read_csv(path + r"\key_word_judgement_data_set.csv")

    both_num = df_data_set.shape[0]  # 总共样本数
    corr_num = np.sum(list(df_data_set['flag']))  # 统计flag为1的个数

    uncorr_data_set = df_data_set[df_data_set.flag != 1]
    corr_data_set = df_data_set[df_data_set.flag == 1]
    uncorr_data_set_num = uncorr_data_set.shape[0]

    max_n_times = both_num // corr_num  # n_times的最大值

    if n_times > max_n_times:
        print("n is too large!")
        return 0

    if get_method == 1:  # 随机取样n_times取样

        get_n_uncorr_data_set = uncorr_data_set.take(np.random.permutation(uncorr_data_set_num)[:n_times * corr_num])
        training_data_set = get_n_uncorr_data_set.append(corr_data_set)
        training_data_set.to_csv(path + r'\random_training_data_set.csv', encoding='utf-8', index=False)
        #print(get_n_uncorr_data_set.shape[0])
        #print(training_data_set.shape[0])

    elif get_method == 2:  # 文件分层取样

        uncorr_data_set_num_get = n_times * corr_num  # 需要取的不相关样本取样个数
        get_ratio_from_vary_file = uncorr_data_set_num_get / uncorr_data_set_num
        # print(get_ratio_from_vary_file)

        weibo_very_file_name_set = set(list(df_data_set['from']))
        # print(weibo_very_file_name_set)

        uncorr_weibo_very_file_num = dict()

        for file_name in weibo_very_file_name_set:
            uncorr_weibo_very_file_num[file_name] = np.count_nonzero(list(uncorr_data_set['from'] == file_name))
        # print(uncorr_weibo_very_file_num)

        weibo_very_file_get_num = dict()
        for file_name in weibo_very_file_name_set:  # 计算需要从各个文件中抽取的数量,四舍五入
            weibo_very_file_get_num[file_name] = int(
                round(uncorr_weibo_very_file_num[file_name] * get_ratio_from_vary_file))
        # print(weibo_very_file_get_num)

        training_layer_data_set = DataFrame()  # 创建一个空dataframe

        for file_name in weibo_very_file_name_set:  # 从各个文件中进行抽取样本
            vary_file_data_set = uncorr_data_set[uncorr_data_set['from'] == file_name]
            temp_data_set = vary_file_data_set.take(
                np.random.permutation(uncorr_weibo_very_file_num[file_name])[:weibo_very_file_get_num[file_name]])
            training_layer_data_set = training_layer_data_set.append(temp_data_set)

        training_layer_data_set = training_layer_data_set.append(corr_data_set)

        # print(training_layer_data_set.shape[0])
        training_layer_data_set.to_csv(path + r"\layer_training_set.csv", encoding="utf-8", index=False)
    else:
        print("get_method value is wrong")


# 计算词频矩阵，存储的结构是稀疏矩阵
def countVectorizer(path):
    df_data_set = pd.read_csv(path + r"\layer_training_set.csv")
    weibo_content_list = list(df_data_set['微博内容'])
    vectorizer = CountVectorizer()
    count_data_set = vectorizer.fit_transform(weibo_content_list)  # 计算词频矩阵
    # print(count_data_set)
    # print((count_data_set).shape)
    return count_data_set


# 特征提取，利用卡方检验方法
def feature_extraction_CHI(path, count_data_set, how_many_featrure=30):
    print("feature_extraction_CHI")
    df_data_set = pd.read_csv(path + r"\layer_training_set.csv")
    flag_list = list(df_data_set['flag'])
    '''
    training_data_set, shape_training_data_set = chi2(count_data_set, flag_list)
    print(training_data_set)
    print(np.mat(training_data_set).shape)
    print(shape_training_data_set)
    '''
    new_data_set = SelectKBest(chi2, how_many_featrure).fit_transform(count_data_set, flag_list)
    # print(new_data_set.shape)
    # print(new_data_set)
    print(new_data_set.shape)
    print(len(flag_list))
    return new_data_set, flag_list

# 特征提取，利用互信息方法
def feature_extraction_mutual_info(path, count_data_set, how_many_featrure=30):
    print("feature_extraction_mutual_info")
    df_data_set = pd.read_csv(path + r"\layer_training_set.csv")
    flag_list = list(df_data_set['flag'])
    print("hello")
    '''
    training_data_set, shape_training_data_set = chi2(count_data_set, flag_list)
    print(training_data_set)
    print(np.mat(training_data_set).shape)
    print(shape_training_data_set)
    '''
    new_data_set = SelectKBest(mutual_info_classif, how_many_featrure).fit_transform(count_data_set, flag_list)
    print(new_data_set.shape)
    print(len(flag_list))
    return new_data_set, flag_list



# 划分训练集和测试集3:1划分
# 数据集前面都是0，后面都是1
def training_test_data_set_get(path, data_set, flag_list):
    print("training_test_data_set_get")
    total_len = (data_set.shape)[0]
    corr_len = np.sum(flag_list)
    uncorr_len = total_len - corr_len

    # print(total_len)
    # print(corr_len)
    # print(uncorr_len)
    corr_test_data_set_size = corr_len // 4
    uncorr_test_data_set_size = uncorr_len // 4

    # print(corr_test_data_set_size)
    # print(uncorr_test_data_set_size)

    corr_training_data_set_size = corr_len - corr_test_data_set_size
    uncorr_training_data_set_size = uncorr_len - uncorr_test_data_set_size

    # print(corr_training_data_set_size)
    # print(uncorr_training_data_set_size)


    uncorr_test_data_set = data_set[: uncorr_test_data_set_size]
    uncorr_training_data_set = data_set[uncorr_test_data_set_size: uncorr_len]

    # print(uncorr_test_data_set.shape)
    # print(uncorr_training_data_set.shape)

    corr_test_data_set = data_set[- corr_test_data_set_size:]
    corr_training_data_set = data_set[- corr_len: -corr_test_data_set_size]

    # print(corr_test_data_set.shape)
    # print(corr_training_data_set.shape)


    test_data_set = np.vstack((uncorr_test_data_set.todense(), corr_test_data_set.todense()))

    # print(test_data_set.todense())

    test_flag_list = [0] * uncorr_test_data_set_size + [1] * corr_test_data_set_size
    # print(test_data_set.shape)
    # print(test_data_set)
    # print(test_flag_list)
    # print(len(test_flag_list))

    training_data_set = np.vstack((uncorr_training_data_set.todense(), corr_training_data_set.todense()))

    training_flag_list = [0] * uncorr_training_data_set_size + [1] * corr_training_data_set_size
    # print(training_data_set.shape)
    # print(training_flag_list)
    # print(len(training_flag_list))

    return training_data_set, training_flag_list, test_data_set, test_flag_list









# 训练模型
'''
1.朴素贝叶斯
2.逻辑斯蒂
3.svm
4.lstm
'''


################
# 贝叶斯模型
################
def bayse_training_moudle(X, y, test_data_set, test_flag_list):
    clf = GaussianNB()
    clf.fit(X, y)
    pre_flag_list = clf.predict(test_data_set)
    error_list = [pre_flag_list - test_flag_list]
    abs_list = map(abs, error_list)
    print("bayse:", end="")
    error = np.sum(list(abs_list))
    print(1 - error / len(pre_flag_list))


################
# logistic模型
################
def logistic_training_moudle(X, y, test_data_set, test_flag_list):
    clf = LogisticRegression(penalty='l2')
    clf.fit(X, y)
    pre_flag_list = clf.predict(test_data_set)
    error_list = [pre_flag_list - test_flag_list]
    abs_list = map(abs, error_list)
    print("logistic:", end="")
    #print(list(abs_list))
    error = np.sum(list(abs_list))
    print(1 - error / len(pre_flag_list))


################
# svm模型
################
def svm_training_moudle(X, y, test_data_set, test_flag_list):
    clf = SVC(C=0.99, kernel='linear')
    clf.fit(X, y)
    pre_flag_list = clf.predict(test_data_set)
    error_list = [pre_flag_list - test_flag_list]
    abs_list = map(abs, error_list)
    print("svm:", end="")
    #print(list(abs_list))
    error = np.sum(list(abs_list))
    print(1 - error / len(pre_flag_list))

#################
# lstm
#################
def lstm_training_moudle(X, y, test_data_set, test_flag_list):
    print('Build model...')
    model = Sequential()
    #model.add(Embedding(len(dict) + 1, 256))
    #model.add(LSTM(256, 128))  # try using a GRU instead, for fun
    #model.add(Dropout(0.5))
    #model.add(Dense(128, 1))
    #model.add(Activation('sigmoid'))

    #model.compile(loss='binary_crossentropy', optimizer='adam', class_mode="binary")
    X = np.array(X)
    y = np.array(y)

    model.add(Dense(units=64, input_dim=30))
    model.add(Activation("relu"))
    model.add(Dense(units=1))
    #model.add(Activation("sigmoid"))
    model.compile(loss='binary_crossentropy', optimizer='adam')
    model.fit(X, y, epochs=10, batch_size=16)

    pre_flag_ndarray = model.predict_classes(test_data_set)
    pre_flag_list = pre_flag_ndarray.tolist()
    #print(pre_flag_list)
    pre_flag_list_finally = []
    for item in pre_flag_list:
        pre_flag_list_finally.append(item[0])
    pre_flag_list_result = np.array(pre_flag_list_finally)
    error_list = [pre_flag_list_result - test_flag_list]
    abs_list = map(abs, error_list)
    error = np.sum(list(abs_list))
    print("lstm:", end="")
    print(1 - error / len(pre_flag_list))


# 统计该文档有多少个不一样的词
def count_diff_word_num(path):
    df_data_set = pd.read_csv(path + r"\drop_stopword_data_set.csv")
    count_dict = {}
    i = 0
    list_weibo_content = list(df_data_set['微博内容'])
    for item in list_weibo_content:
        for item_word in item.split(' '):
            if item_word not in count_dict:
                count_dict[item_word] = 1
            else:
                count_dict[item_word] += 1
    print("diffwords:", end="")
    print(len(count_dict))


def main():
    path = r'G:\weibo_project\maoxian'
    loadDataSetSave(path)
    transmitContent(path)
    cleanDateSet(path)
    cutWords(path)
    drop_stop_words(path)
    count_diff_word_num(path)
    #############################
    # 关键字抽取
    key_word_judgement(path)
    #key_word_judgement_using_lay_word(path)
    #############################

    #############################
    #
    get_n_uncorr_set(path, 2, 2)
    #############################
    count_data_set = countVectorizer(path)
    ###
    # 两种特征提取
    #feature_data_set, flag_list = feature_extraction_CHI(path, count_data_set, 30)
    feature_data_set, flag_list = feature_extraction_mutual_info(path, count_data_set, 30)
    ###
    X, y, test_data_set, test_flag_list = training_test_data_set_get(path, feature_data_set, flag_list)
    bayse_training_moudle(X, y, test_data_set, test_flag_list)
    logistic_training_moudle(X, y, test_data_set, test_flag_list)
    svm_training_moudle(X, y, test_data_set, test_flag_list)
    lstm_training_moudle(X, y, test_data_set, test_flag_list)

main()
