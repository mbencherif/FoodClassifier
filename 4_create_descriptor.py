from multiprocessing import Pool

import os
import itertools
from numpy import concatenate
from cv2 import getNumberOfCPUs
from utils import get_train_test, get_histogram, get_spatial_pyramid, save_pickle, load_pickle, get_sift_lowe, get_sift, removing_null

from sklearn.cluster import MiniBatchKMeans

import warnings
warnings.filterwarnings("ignore")

TEST = True
SAVE = True
LOWE = False

descriptor = "SIFT"
descriptor = "spSIFT"

if TEST:
    prefix = "%s_%s_" % (descriptor, "test")
else:
    prefix = "%s_%s_" % (descriptor, "full")

train_images, train_labels, test_images, test_labels = get_train_test(TEST)

if descriptor == "SIFT":
    if (os.path.isfile(prefix%"kmeans")):
        kmeans = load_pickle(prefix + "kmeans.pkl")
    else:
        pool = Pool(getNumberOfCPUs()-2)

        if LOWE:
            print " [!] Lowe's SIFT"
            train_sift_with_null = pool.map(get_sift_lowe, train_images)
            test_sift_with_null = pool.map(get_sift_lowe, test_images)
        else:
            print " [!] OpenCV2's SIFT"
            train_sift_with_null = pool.map(get_sift, train_images)
            test_sift_with_null = pool.map(get_sift, test_images)

        pool.close()
        pool.join()
        pool.terminate()

        del pool

        train_sift = removing_null(train_sift_with_null, train_labels)
        reduced_train_sift = concatenate(train_sift, axis = 0)

        test_sift = removing_null(test_sift_with_null, test_labels)
        reduced_test_sift = concatenate(test_sift, axis = 0)

        all_sift = concatenate((reduced_train_sift,reduced_test_sift), axis=0)
        nfeatures = all_sift.shape[0]
        k = 1000

        kmeans = MiniBatchKMeans(n_clusters = k,
                                init       ='k-means++',
                                n_init     = 10,
                                max_iter   = 100,
                                init_size  = 1000,
                                batch_size = 1000)

        kmeans.fit(all_sift)
        if SAVE:
            save_pickle(prefix + "kmeans.pkl",kmeans)

    #train_predicted = kmeans.predict(reduced_train_sift)
    #test_predicted = kmeans.predict(reduced_test_sift)

    #train_hist_features = get_histogram(k, train_sift, train_predicted)
    #test_hist_features = get_histogram(k, test_sift, test_predicted)
elif descriptor == "spSIFT":
    k = 1000

    if (os.path.isfile(prefix + "train_sift.pkl")):
        kmeans = load_pickle(prefix + "kmeans.pkl")
        train_sift = load_pickle(prexif + "train_sift.pkl")
        test_sift = load_pickle(prexif + "test_sift.pkl")

        reduced_train_sift = concatenate(train_sift, axis = 0)
        reduced_test_sift = concatenate(test_sift, axis = 0)

        all_sift = concatenate((reduced_train_sift,reduced_test_sift), axis=0)
        nfeatures = all_sift.shape[0]
    else:
        pool = Pool(getNumberOfCPUs()-2)

        if LOWE:
            print " [!] Lowe's SIFT"
            train_sift_with_null = pool.map(get_sift_lowe, train_images)
            test_sift_with_null = pool.map(get_sift_lowe, test_images)
        else:
            print " [!] OpenCV2's SIFT"
            train_sift_with_null = pool.map(get_sift, train_images)
            test_sift_with_null = pool.map(get_sift, test_images)

        pool.close()
        pool.join()
        pool.terminate()

        del pool

        train_sift = removing_null(train_sift_with_null, train_labels)
        reduced_train_sift = concatenate(train_sift, axis = 0)

        test_sift = removing_null(test_sift_with_null, test_labels)
        reduced_test_sift = concatenate(test_sift, axis = 0)

        if SAVE and not os.path.isfile(prefix + "train_sift.pkl"):
            save_pickle(prefix + "train_sift.pkl",train_sift)
            save_pickle(prefix + "test_sift.pkl",test_sift)

        all_sift = concatenate((reduced_train_sift,reduced_test_sift), axis=0)
        nfeatures = all_sift.shape[0]

        if (os.path.isfile(prefix + "kmeans.pkl")):
            print "[^] Skip Kmeans"
            kmeans = load_pickle(prefix + "kmeans.pkl")
        else:
            kmeans = MiniBatchKMeans(n_clusters = k,
                                    init       ='k-means++',
                                    n_init     = 10,
                                    max_iter   = 100,
                                    init_size  = 1000,
                                    batch_size = 1000)

            print " [!] Kmeans fitting"
            kmeans.fit(all_sift)
            if SAVE:
                save_pickle(prefix + "kmeans.pkl",kmeans)

    print " [!] Kmeans prediction"
    train_predicted = kmeans.predict(reduced_train_sift)
    test_predicted = kmeans.predict(reduced_test_sift)

    print " [!] Making histogram"
    if not os.path.isfile(prefix+"train_hist_features.pkl"):
        train_hist_features = get_histogram(k, train_sift, train_predicted)
        if SAVE and not os.path.isfile(prefix+"train_hist_features.pkl"):
            print " [!] Saving histogram 1"
            save_pickle(prefix+"train_hist_features.pkl",train_hist_features)

        del train_hist_features

        test_hist_features = get_histogram(k, test_sift, test_predicted)
        if SAVE and not os.path.isfile(prefix+"test_hist_features.pkl"):
            print " [!] Saving histogram 2"
            save_pickle(prefix+"test_hist_features.pkl",test_hist_features)

        del test_hist_features

    if not os.path.isfile(prefix+"train_spp_hist.pkl"):
        print " [!] Making SPP histogram 1"

        """print " [!] Making SPP histogram 1 : %s, %s" % (kmeans.cluster_centers_, all_sift.shape)
        train_spp_hist = []
        for image in train_images:
            train_spp_hist.append(get_spatial_pyramid(image, kmeans.cluster_centers_, all_sift.shape[0]))"""
        pool = Pool(2)

        tmp = itertools.repeat(kmeans.cluster_centers_)
        tmp2 = itertools.repeat(all_sift.shape[0])
        train_spp_hist = pool.map(get_spatial_pyramid, itertools.izip(train_images, tmp, tmp2))

        pool.close()
        pool.join()
        pool.terminate()
        del pool

        if SAVE:
        #if True:
            print " [!] Saving SPP histogram 1"
            save_pickle(prefix+"train_spp_hist.pkl",train_spp_hist)

        del train_spp_hist

    if not os.path.isfile(prefix+"test_spp_hist.pkl"):
        """test_spp_hist = []
        for image in test_images:
            train_spp_hist.append(get_spatial_pyramid(image, kmeans.cluster_centers_, all_sift.shape[0]))"""
        print " [!] Making SPP histogram 2"
        pool = Pool(2)

        tmp = itertools.repeat(kmeans.cluster_centers_)
        tmp2 = itertools.repeat(all_sift.shape[0])
        test_spp_hist = pool.map(get_spatial_pyramid, itertools.izip(test_images, tmp, tmp2))

        pool.close()
        pool.join()
        pool.terminate()
        del pool

        if SAVE:
            print " [!] Saving SPP histogram 1"
            save_pickle(prefix+"test_spp_hist.pkl",test_spp_hist)
