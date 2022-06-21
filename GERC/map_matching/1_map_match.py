# -*- coding: utf-8 -*-
# Todo: 给出一个GPS点（116.46036, 39.89108 ），判断所在的网格id
# @Time    : 2022/5/19 19:05
# @Author  : chen
# @File    : 1_map_match.py
# @Software: PyCharm
import math

from road_prediction.basic_method.grid_basic import get_grid_id
from road_prediction.util import const

a = 6378245.0  # 长半轴
pi = 3.1415926535897932384626  # π
ee = 0.00669342162296594323  # 扁率


def get_grid(x, y):
    grid_x1 = (x - const.min_lon) / const.w
    grid_y1 = (y - const.min_lat) / const.h
    print("grid_x1:", grid_x1)
    print("grid_y1:", grid_y1)
    x_index = math.ceil(grid_x1)
    y_index = math.ceil(grid_y1)
    print("x_index:", x_index)
    print("y_index:", y_index)
    grid_id = get_grid_id(x_index, y_index, const.m)
    return grid_id


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 * math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 * math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def wgs84togcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]


def mercatortowgs84(x,y):
    """
    墨卡托投影坐标转回wgs84
    :param x:
    :param y:
    :return:
    """
    lng = x / 20037508.34 * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(y / 20037508.34 * 180 * math.pi / 180)) - math.pi / 2)
    return lng,lat


if __name__ == '__main__':
    const.m = 810
    const.n = 1046
    const.min_lon = 115.423411
    const.min_lat = 39.4408
    const.h = 39.4428 - 39.4408
    const.w = 115.425411 - 115.423411

    test_point = [116.389745,39.988037]
    [mglng, mglat] = wgs84togcj02(test_point[0], test_point[1])
    print("转换后的坐标为：", [mglat, mglng])

    grid_id = get_grid(test_point[0], test_point[1])
    print("grid_id:", grid_id)
    # 116.483411 39.900800000000004
    test_point_mer = [441244.86360899, 4372241.54599674]
    lng, lat = mercatortowgs84(test_point_mer[0], test_point_mer[1])
    wgs_lng, wgs_lat = wgs84togcj02(lng, lat)
    print("墨儿卡转换后的坐标为：", [wgs_lat, wgs_lng])

