#!/bin/bash
app_path="$( cd "$(dirname ${BASH_SOURCE})" ; pwd -P )"
app_name="whenet"

# ************************convert CIDR to netmask****************************************
# Description:  convert CIDR to netmask
# $1: CIDR
# ******************************************************************************
function cidr2mask()
{
   # Number of args to shift, 255..255, first non-255 byte, zeroes
   set -- $(( 5 - ($1 / 8) )) 255 255 255 255 $(( (255 << (8 - ($1 % 8))) & 255 )) 0 0 0
   [ $1 -gt 1 ] && shift $1 || shift
   echo ${1-0}.${2-0}.${3-0}.${4-0}
}

function check_ip_addr()
{
    ip_addr=$1
    ip_addr=$(echo "$ip_addr" | grep "^[0-9]\{1,3\}\.\([0-9]\{1,3\}\.\)\{2\}[0-9]\{1,3\}$")
    if [ -z "$ip_addr" ]
    then
	    echo "ip_addr $ip_check invalid"
        return 1
    fi

    for num in `echo ${ip_addr} | sed "s/./ /g"`
    do
        if [ $num -gt 255 ] || [ $num -lt 0 ]
        then
            return 1
        fi
   done
   return 0
}

function check_board_ip()
{
    #check format of remost_host ip
    board_ip=$(cat ${app_path}/whenet.conf | grep "atlas200dk_board_ip" | awk -F'[ =]+' '{print $2}')
	board_ip=$(echo $board_ip | sed -e 's/\r//' | sed -e 's/\n//' | sed -e 's/ //')
    if [[ "$board_ip" = "" ]];then
        echo "please check your whenet.conf to make sure that each parameter has a value"
        return 1
    fi
    check_ip_addr $board_ip
    if [ $? -ne 0 ];then
        echo "ERROR: invalid board_ip ip, please check your settings in configuration file"
        return 1
    fi 
}

function check_python3_lib()
{
    echo "Check python3 libs ......"

    tornado_obj=$(cat ${app_path}/presenterserver/requirements | grep tornado | awk -F'[ =]+' '{print $2}')
    if [ $? -ne 0 ];then
        echo "ERROR: please check your env."
        return 1
    elif [ 5.1.0 = ${tornado_obj} ];then
		tornado_obj=5.1
    fi


    protobuf_obj=$(cat ${app_path}/presenterserver/requirements | grep protobuf | awk -F'[ =]+' '{print $2}')
    if [ $? -ne 0 ];then
        echo "ERROR: please check your env."
        return 1
    fi
        
    numpy_obj=$(cat ${app_path}/presenterserver/requirements | grep numpy | awk -F'[ =]+' '{print $2}')
    if [ $? -ne 0 ];then
        echo "ERROR: please check your env."
        return 1
    fi
    
    if tornado=$(python3 -c "import tornado;print(tornado.version)" 2>/dev/null);then
		if [ ${tornado} != ${tornado_obj} ];then
	    	pip3 install tornado==${tornado_obj} 2>/dev/null
     		if [ $? -ne 0 ];then
        		echo "ERROR: install tornado failed, please check your env."
        		return 1
        	fi
		fi
    else
		pip3 install tornado==${tornado_obj} 2>/dev/null
		if [ $? -ne 0 ];then
	    	echo "ERROR: install tornado failed, please check your env."
            return 1
        fi
    fi 

    if protobuf=$(python3 -c "import google.protobuf;print(google.protobuf.__version__)" 2>/dev/null);then
		if [ ${protobuf} != ${protobuf_obj} ];then
	    	pip3 install protobuf==${protobuf_obj} 2>/dev/null
     	    if [ $? -ne 0 ];then
        		echo "ERROR: install protobuf failed, please check your env."
        		return 1
            fi
		fi
    else
		pip3 install protobuf==${protobuf_obj} 2>/dev/null
		if [ $? -ne 0 ];then
	    	echo "ERROR: install protobuf failed, please check your env."
            return 1
        fi
    fi 
    
    if numpy=$(python3 -c "import numpy;print(numpy.__version__)" 2>/dev/null);then
		if [ ${numpy} != ${numpy_obj} ];then
	    	pip3 install numpy==${numpy_obj} 2>/dev/null
     	    if [ $? -ne 0 ];then
        		echo "ERROR: install numpy failed, please check your env."
        		return 1
            fi
		fi
    else
		pip3 install numpy==${numpy_obj} 2>/dev/null
		if [ $? -ne 0 ];then
	    	echo "ERROR: install numpy failed, please check your env."
            return 1
        fi
    fi 
    

    echo "python3 libs have benn prepared."
}

function parse_presenter_view_ip()
{
    presenter_view_ip="127.0.0.1"
    return 0
}

function check_ips_in_same_segment()
{
    ip=$1
    mask=$2
    board_ip=$3

    OLD_IFS_IP="${IFS}"
    IFS="."
    board_ip_attr=(${board_ip})
    ip_attr=(${ip})
    mask_attr=(${mask})
    IFS=${OLD_IFS_IP}
    for i in `seq 0 3`
    do
        ((calc_remote=${board_ip_attr[${i}]}&${mask_attr[${i}]}))
        ((calc_ip=${ip_attr[${i}]}&${mask_attr[${i}]}))

        if [[ calc_remote -ne calc_ip ]];then
            return 1
        fi
    done
    return 0
}

# ************************parse presenter_altasdk ip****************************
# Description:  parse presenter_altasdk ip right or not
# $1: board_ip ip
# ******************************************************************************

function parse_presenter_altasdk_ip()
{
    valid_ips=""
    board_ip=$1
    for ip_info in `/sbin/ip addr | grep "inet " | awk -F ' ' '{print $2}'`
    do
        ip=`echo ${ip_info} | awk -F '/' '{print $1}'`
        cidr=`echo ${ip_info} | awk -F '/' '{print $2}'`

        valid_ips="${valid_ips}\t${ip}\n"
        mask=`cidr2mask ${cidr}`
        if [[ ${ip}"X" == "X" ]];then
            continue
        fi
        check_ips_in_same_segment ${ip} ${mask} ${board_ip}
        if [[ $? -eq 0 ]];then
            presenter_atlasdk_ip=${ip}
            echo "Find ${presenter_atlasdk_ip} which is in the same segment with ${board_ip}."
            break
        fi
    done

    
    if [[ ${presenter_atlasdk_ip}"X" != "X" ]];then
        return 0
    fi
    
    echo "Can not find ip in the same segment with ${board_ip}."
    while [[ ${presenter_atlasdk_ip}"X" == "X" ]]
    do
        echo -en "Current environment valid ip list:\n${valid_ips}Please choose one which can connect to Atlas DK Developerment Board:"
        read presenter_atlasdk_ip
        if [[ ${presenter_atlasdk_ip}"X" != "X" ]];then
            check_ip_addr ${presenter_atlasdk_ip}
            if [[ $? -ne 0 ]];then
                echo "Invlid ip, please choose again..."
                presenter_atlasdk_ip=""
            else
                #使用grep检测字段，如果没有找到相应的字段，使用$?会返回非零值
                ret=`/sbin/ifconfig | grep ${presenter_atlasdk_ip}`
                if [[ $? -ne 0 ]];then
                    presenter_atlasdk_ip=""
                fi
            fi
        fi
    done
    return 0
}


function main()
{
    stop_pid=`ps -ef | grep "presenter_server\.py" | grep "${app_name}" | awk -F ' ' '{print $2}'`
    if [[ ${stop_pid}"X" != "X" ]];then
        echo -e "\033[33mNow do presenter server configuration, kill existing presenter process: kill -9 ${stop_pid}.\033[0m"
        kill -9 ${stop_pid}
    fi

    check_python3_lib
    if [ $? -ne 0 ];then
		return 1
    fi

    #get and check format of remost_host ip
    check_board_ip
    if [ $? -ne 0 ];then
	return 1
    fi 

    parse_presenter_altasdk_ip ${board_ip}

    parse_presenter_view_ip

    #1.检查完毕ip之后，将ip的数值复制到config.config 
    echo "Use ${presenter_atlasdk_ip} to connect to Atlas DK Developerment Board..."
    sed -i "s/presenter_server_ip=[0-9.]*/presenter_server_ip=${presenter_atlasdk_ip}/g" ${app_path}/presenterserver/whenet/config/config.conf
    
    echo "Use ${presenter_view_ip} to show information in browser..."
    sed -i "s/web_server_ip=[0-9.]*/web_server_ip=${presenter_view_ip}/g" ${app_path}/presenterserver/whenet/config/config.conf
    
    echo "Finish to prepare ${app_name} presenter server ip configuration."
    
    python3 ${app_path}/presenterserver/presenter_server.py --app ${app_name} &

    return 0
}
main
