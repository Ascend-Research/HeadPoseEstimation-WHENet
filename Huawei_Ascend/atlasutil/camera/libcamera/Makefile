TOPDIR      := $(patsubst %,%,$(CURDIR))

ifndef DDK_HOME
$(error "Can not find DDK_HOME env, please set it in environment!.")
endif

LOCAL_MODULE_NAME := libcamera.so
CC := aarch64-linux-gnu-g++


LOCAL_DIR  := .
OUT_DIR = out
OBJ_DIR = $(OUT_DIR)/obj
DEPS_DIR  = $(OUT_DIR)/deps
LOCAL_LIBRARY=$(OUT_DIR)/$(LOCAL_MODULE_NAME)
OUT_INC_DIR = $(OUT_DIR)/include

INC_DIR = \
	-I$(LOCAL_DIR)/include \
	-I$(DDK_HOME)/include/inc \
        -I$(DDK_HOME)/include/libc_sec/include \
        -I$(DDK_HOME)/include/inc/hiaiengine \
        -I$(DDK_HOME)/include/third_party/opencv/include 
	

CC_FLAGS := $(INC_DIR) -std=c++11 -fPIC -Wall -O2
LNK_FLAGS := \
	-L$(NPU_DEVICE_LIB) \
	-lmedia_mini \
	-lhiai_common \
	-lDvpp_api \
        -lopencv_world \
	-shared

SRCS := $(patsubst $(LOCAL_DIR)/%.cpp, %.cpp, $(shell find $(LOCAL_DIR) -name "*.cpp"))
OBJS := $(addprefix $(OBJ_DIR)/, $(patsubst %.cpp, %.o,$(SRCS)))

ALL_OBJS := $(OBJS)

all: do_pre_build do_build

do_pre_build:
	$(Q)echo - do [$@]
	$(Q)mkdir -p $(OBJ_DIR)
	$(Q)mkdir -p $(OUT_INC_DIR)

do_build: $(LOCAL_LIBRARY) | do_pre_build
	$(Q)echo - do [$@]

$(LOCAL_LIBRARY): $(ALL_OBJS)
	$(Q)echo [LD] $@
	$(Q)$(CC) $(CC_FLAGS) -o $@ $^ -Wl,--whole-archive -Wl,--no-whole-archive -Wl,--start-group -Wl,--end-group $(LNK_FLAGS)


$(OBJS): $(OBJ_DIR)/%.o : %.cpp | do_pre_build
	$(Q)echo [CC] $@
	$(Q)mkdir -p $(dir $@)
	$(Q)$(CC) $(CC_FLAGS) $(INC_DIR) -c -fstack-protector-all $< -o $@


clean:
	rm -rf $(TOPDIR)/out
