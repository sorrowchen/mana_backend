#!/usr/bin/env python
#coding: utf-8

import simplejson
import eventlet

from mana_http import HttpCon
import mana_log
LOG = mana_log.GetLog(__name__)

import  mana_conf
CONF = mana_conf.GetConf()

from mana_public import DATA_QUEUE
from mana_public import data_item
from mana_public import period_task

def admin_collection():
    pool = eventlet.GreenPool()
    interval = CONF.get('cycletime')
    LOG.info("Begin admin-collection data thread,cycletime is %ss" %interval)
    task  = period_task("admin-task", interval)
    task.set_fun(period_run, pool)
    task.run()

def period_run(pool):
    _collection(pool)
    pool.waitall()

def _collection(pool):
    try:
        regions = CONF.get('regions')
        for region in regions:
            instances = get_instances_from_api(region)
            for instance in instances:
                _collection_per_instance(region, instance, pool)
    except Exception, e:
        LOG.error(e)

def _collection_per_instance(region, instance, pool):
    try:
        for (alarm_obj, thd) in CONF.get('alarm_list'):
            threshold = float(thd) 
            pool.spawn_n(_collection_datas, region, instance, alarm_obj, threshold)
    except Exception, e:
        LOG.error(e) 

def get_instances_from_api(region):
    url = CONF.get('url').get('get_all_instance_url') %region
    api_host = CONF.get('api_host')
    api_port = CONF.get('api_port')
    try:
        httpclient = HttpCon(api_host, api_port, url, "GET")
        body = httpclient.get()
        if body:
            instances = simplejson.loads(body).get('data')
    except Exception, e:
        LOG.error(e)
        return None
    return instances 

def _collection_datas(region, instance, alarm_obj, threshold):
    email_receiver = CONF.get('email_receiver')
    phone_receiver = CONF.get('phone_receiver')
    contacts = {"email_receiver":email_receiver, "phone_receiver":phone_receiver}
    try:
        instance_id = instance.get('instance_id')
        data = get_datas_from_api(region, instance_id, alarm_obj)
        item = data_item(instance, alarm_obj , threshold, region, data, contacts)
        DATA_QUEUE.put(item)
    except Exception, e:
        LOG.error(e)  

def get_datas_from_api(region, instance_id, alarm_obj):
    time = CONF.get('cycletime')
    url = CONF.get('url').get('get_metric_url') %(region, alarm_obj, instance_id, time)
    api_host = CONF.get('api_host')
    api_port = CONF.get('api_port')
    try:
        httpclient = HttpCon(api_host, api_port, url, "POST")
        body = httpclient.get()
        if body:
            data = simplejson.loads(body)
    except Exception, e:
        LOG.error(e)
        return None
    return data
    


"""
def collection():
    interval = CONF.get('cycletime')
    LOG.info("Begin to get collection data thread,cycletime is %ss" %interval)
    while True:
        try:
            time_pre = time.time()
            _collection()
            time_now = time.time()
            monitor_time = time_now - time_pre
            if monitor_time < interval:
                LOG.info("Get data time = %ss, DATA_QUEUE's size = %s" %(monitor_time,DATA_QUEUE.qsize()))
                time.sleep(interval + time_pre - time_now)
            else:
                LOG.warn("Get data use too long time = %ss,  DATA_QUEUE's size = %s" %(monitor_time,DATA_QUEUE.qsize()))
        except Exception, e:
            LOG.error(e)

def _collection():
    try:
        regions = CONF.get('regions')
        for region in regions:
            instances = get_instances_from_api(region)
            for instance in instances:
                get_datas(region, instance)
    except Exception, e:
        LOG.error(e)

def get_datas(region, instance):
    try:
        for (alarm_obj, thd) in CONF.get('alarm_list'):
            instance_id = instance.get('instance_id')
            datas = get_datas_from_api(region, instance_id, alarm_obj)
            threshold = float(thd) 
            item = data_item(instance, alarm_obj , threshold, region, datas)
            DATA_QUEUE.put(item)
    except Exception, e:
        LOG.error(e) 

def get_instances_from_api(region):
    url = CONF.get('url').get('get_all_instance_url') %region
    api_host = CONF.get('api_host')
    api_port = CONF.get('api_port')
    try:
        httpclient = HttpCon(api_host, api_port, url, "GET")
        body = httpclient.get()
        if body:
            instances = simplejson.loads(body).get('data')
    except Exception, e:
        LOG.error(e)
        return NULL
    return instances 

def get_datas_from_api(region, instance, alarm_obj):
    url = CONF.get('url').get('get_metric_url') %(region, alarm_obj, instance)
    api_host = CONF.get('api_host')
    api_port = CONF.get('api_port')
    try:
        httpclient = HttpCon(api_host, api_port, url, "POST")
        body = httpclient.get()
        if body:
            data = simplejson.loads(body)
    except Exception, e:
        LOG.error(e)
        return NULL
    return data
"""

if __name__ == "__main__":
    admin_collection()

