#!/bin/sh

set -e
SENTINEL=/tmp/rabbit_ceil_ok
if [ ! -e $SENTINEL ] ; then
    USER=$1
    PASSWORD=$2
    #Tag with administrator in order to add ability to create and delete users, create and delete permissions through http api
    rabbitmqctl add_user $USER $PASSWORD || true
    rabbitmqctl change_password $USER $PASSWORD
    rabbitmqctl set_user_tags $USER administrator management
    rabbitmqctl add_vhost /zenoss || true
    rabbitmqctl clear_permissions -p /zenoss $USER
    rabbitmqctl set_permissions -p /zenoss $USER '.*' '.*' '.*'
    rabbitmqadmin --port=45672 --vhost=/zenoss --username=$USER --password=$PASSWORD declare exchange name=zenoss.openstack.ceilometer type=topic
    rabbitmqctl delete_user guest || true
    touch $SENTINEL
fi
