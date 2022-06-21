# -*- coding: utf-8 -*-
# Todo: 给出一个GPS点（116.46036, 39.89108 ），判断所在的网格id。匹配路段所经过的网格ID。
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


def get_id(x, y, m=810):
    id_res = (x - 1) * m + y
    return id_res


def get_grid_id(x, y):
    # 输入GPS点坐标
    # 获得GPS点所在的网格id
    # m = 810
    # n = 1046
    min_lon = 115.423411
    min_lat = 39.4408
    [min_lon, min_lat] = wgs84togcj02(min_lon, min_lat)
    h = 39.4428 - 39.4408
    w = 115.425411 - 115.423411
    grid_x1 = math.ceil((x - min_lon) / w)
    grid_y1 = math.ceil((y - min_lat) / h)

    id_res = get_id(grid_x1, grid_y1)

    return grid_x1, grid_y1, id_res


def get_gps_grid_id(lon, lat, grid_json, road_json):
    """
    输入GPS，返回所在道路的osmid
    Args:
        lon: 经度
        lat: 纬度

    Returns:此GPS点所在的网格ID

    """
    x_index, y_index, id_res = get_grid_id(lon, lat)
    road_name, road_osm = get_gps_road(id_res, lon, lat, x_index, y_index, grid_json, road_json)
    return road_name, road_osm


def get_pointLineDis(road_ls, point):
    """
    输入道路[id,x1,y1,x2,y2]的集合，以及点的坐标，输出最小距离[min_road_id, min_D]
    Args:
        road_ls:
        point:

    Returns:

    """
    dis_list = []
    for road in road_ls:
        road_id = road[0]
        road_line = [float(i) for i in road[1:]]
        # print("road的信息为：", road_line)
        # print("road的序号为：", road_id)
        D = get_distance_point2line(point, road_line)
        # print("GPS点距离道路的距离为：", D)
        dis_list.append(D)
    min_D = min(dis_list)
    min_index = dis_list.index(min_D)   # 最小值的索引
    min_road_id = road_ls[min_index][0]

    # 返回距离最小的道路
    return [min_road_id, min_D]


def get_road_Node(road_json, road):
    """
    输入道路json文件和道路id，返回道路[id, start_x, start_y, end_x, end_y]
    Args:
        road_json:
        road:

    Returns:

    """
    start_x = road_json[road]['START_X']
    start_y = road_json[road]['START_Y']
    end_x = road_json[road]['END_X']
    end_y = road_json[road]['END_Y']
    return [road, start_x, start_y, end_x, end_y]


def get_road_node_ls(road_ls, road_json):
    """
    输入路段序号列表，返回道路起始点坐标集合[[1,[start,end]],[5,[start,end]]...]
    Args:
        road_ls:
        road_json:

    Returns:

    """
    road_list = []
    for r in road_ls:
        road = get_road_Node(road_json, r)
        road_list.append(road)
    return road_list


def get_distance_point2line(point, line):
    """
    GPS点到一条直线的距离
    Args:
        point:
        line:

    Returns:

    """
    """ Args: point: [x0, y0] line: [x1, y1, x2, y2] """
    line_point1, line_point2 = np.array(line[0:2]), np.array(line[2:])
    vec1 = line_point1 - point
    vec2 = line_point2 - point
    distance = np.abs(np.cross(vec1, vec2)) / np.linalg.norm(line_point1 - line_point2)
    return distance


def get_around_grids(x, y):
    """
    给一个网格的横坐标和纵坐标，得到周围8个网格的横坐标和纵坐标
    Args:
        x:
        y:

    Returns:

    """
    around_list = []
    for i in range(x-1, x+2):
        # print("i:", i)
        for j in range(y-1, y+2):
            if i != x & j != y:
                id_res = get_id(i, j)
                around_list.append(id_res)
    return around_list


def get_around_road_name(road_id_list, around_grids, lon, lat, grid_json, road_json):
    """
    根据八个网格的id，得到路段的id，并计算GPS与这些路段的最短距离，返回路段名字。
    如果没有路段，返回null
    Args:
        road_id_list: 中间网格的路段id
        around_grids:
        lon:
        lat:

    Returns:

    """
    road_ls = []
    road_id_list = []
    for grid in around_grids:
        road_ls = str(grid_json[str(grid)]['road_id']).split("|")[:-1]
        road_id_list = road_id_list + road_ls

    if len(road_id_list) != 0:
        # 计算GPS点与各个道路的距离
        point = [lon, lat]
        road_id_list = get_road_node_ls(road_id_list, road_json)

        [road_id, D] = get_pointLineDis(road_id_list, point)
        road_osm = road_json[str(road_id)]['OSMID']
        road_name = road_json[str(road_id)]['name']
        return road_name, road_osm
    else:
        return "null", "none"


def get_gps_road(id_res, lon, lat, x, y, grid_json, road_json):
    """
    根据GPS和网格序号，得到路段名字
    Args:
        id_res: GPS点所在的网格序号
        lon: 经度
        lat: 纬度
        x:网格的横坐标
        y:网格的纵坐标

    Returns:

    """
    # 根据网格ID得到网格内的路段集合
    if id_res < 0:
        return "null", "none"
    road_ls = str(grid_json[str(id_res)]['road_id']).split("|")[:-1]
    # print("id_res:", id_res)
    # # 如果所在的网格存在路段
    if len(road_ls) != 0:
        # 计算GPS点与各个道路的距离
        point = [lon, lat]
        road_ls = get_road_node_ls(road_ls, road_json)

        [road_id, D] = get_pointLineDis(road_ls, point)
        road_osm = road_json[str(road_id)]['OSMID']
        road_name = road_json[str(road_id)]['name']
        return road_name, road_osm
    # 如果网格没有匹配的路段，则看周围8个网格内是否存在路段
    else:
        around_grids = get_around_grids(x, y)
        road_name, road_osm = get_around_road_name(road_ls, around_grids, lon, lat, grid_json, road_json)
        return road_name, road_osm

# if __name__ == '__main__':
#     const.m = 810
#     const.n = 1046
#     const.min_lon = 115.423411
#     const.min_lat = 39.4408
#     const.h = 39.4428 - 39.4408
#     const.w = 115.425411 - 115.423411

#     test_point = [116.389745,39.988037]
#     [mglng, mglat] = wgs84togcj02(test_point[0], test_point[1])
#     print("转换后的坐标为：", [mglat, mglng])

#     grid_id = get_grid(test_point[0], test_point[1])
#     print("grid_id:", grid_id)
#     # 116.483411 39.900800000000004
#     test_point_mer = [441244.86360899, 4372241.54599674]
#     lng, lat = mercatortowgs84(test_point_mer[0], test_point_mer[1])
#     wgs_lng, wgs_lat = wgs84togcj02(lng, lat)
#     print("墨儿卡转换后的坐标为：", [wgs_lat, wgs_lng])

