/**
 * ============================================================================
 *
 * Copyright (C) 2018, Hisilicon Technologies Co., Ltd. All Rights Reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *   1 Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 *
 *   2 Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 *
 *   3 Neither the names of the copyright holders nor the names of the
 *   contributors may be used to endorse or promote products derived from this
 *   software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 * ============================================================================
 */
#include <stdio.h>
#include <stdarg.h>
#include <time.h>
#include <memory>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include "dvpp_image.h"
#include "camera.h"
#include "log.h"

using namespace std;

extern "C" {
#include "driver/peripheral_api.h"
#include "camera.h"

CameraManager g_camera_mgr;

void CameraInit(CameraConfig* config) {
	MediaLibInit();

    g_camera_mgr.config = *config;
	g_camera_mgr.yuv_image_buf = new ImageBuffer(config->width, config->height);

/*
	g_camera_mgr.image_buf.width = config->width;
	g_camera_mgr.image_buf.height = config->height;

	uint32_t stride = ALIGN_UP(config->width, ALIGN_16);
	g_camera_mgr.image_buf.size = ALIGN_UP(YUV420SP_SIZE(stride, config->height), PAGE_SIZE);
	g_camera_mgr.image_buf.data = new (nothrow) uint8_t[g_camera_mgr.image_buf.size + JPEG_ENCODE_ADDR_ALIGN];
        g_camera_mgr.image_buf.data = (unsigned char*) ALIGN_UP((uint64_t ) g_camera_mgr.image_buf.data, 
                                      JPEG_ENCODE_ADDR_ALIGN);
        //g_camera_mgr.image_buf.data = (uint8_t*)HIAI_DVPP_DMalloc(g_camera_mgr.image_buf.size + );
*/
	g_camera_mgr.inited = 1;
}

int ConfigCamera(CameraConfig* config) {
	int ret = SetCameraProperty(config->id, CAMERA_PROP_FPS, &(config->fps));
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Set camera fps failed");
		return STATUS_ERROR;
	}
    ASC_LOG_INFO("Set camera %d fps to %d ok", config->id, config->fps);

	int image_format = CAMERA_IMAGE_YUV420_SP;
	ret = SetCameraProperty(config->id, CAMERA_PROP_IMAGE_FORMAT, &image_format);
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Set camera image format to %d failed", image_format);
		return STATUS_ERROR;
	}
    ASC_LOG_INFO("Set camera %d format ok", config->id);

	// set image resolution.
	CameraResolution resolution;
	resolution.width = config->width;
	resolution.height = config->height;
	ret = SetCameraProperty(config->id, CAMERA_PROP_RESOLUTION,	&resolution);
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Set camera resolution failed");
		return STATUS_ERROR;
	}
    ASC_LOG_INFO("Set camera %d resolution (%d * %d) ok", config->id, config->width, config->height);

	// set work mode
	CameraCapMode mode = CAMERA_CAP_ACTIVE;
	ret = SetCameraProperty(config->id, CAMERA_PROP_CAP_MODE, &mode);
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Set camera mode:%d failed", mode);
		return STATUS_ERROR;
	}
    ASC_LOG_INFO("Set camera %d mode to ACTIVE ok", config->id);

	return STATUS_OK;
}

int Open(CameraConfig* config) {
	if (!g_camera_mgr.inited) {
		CameraInit(config);
	}

	CameraStatus status = QueryCameraStatus(config->id);
	if (status != CAMERA_STATUS_CLOSED) {
		ASC_LOG_ERROR("Query camera %d status error:%d", config->id, status);
		return STATUS_ERROR;
	}

	// Open Camera
	int ret = OpenCamera(config->id);
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Open camera %d failed.", config->id);
		return STATUS_ERROR;
	}

	//Set camera property
	ret = ConfigCamera(config);
	if (ret != STATUS_OK) {
		CloseCamera(config->id);
		ASC_LOG_ERROR("Set camera %d property failed", config->id);
		return STATUS_ERROR;
	}

    ASC_LOG_INFO("Open camera %d success", config->id);

	return STATUS_OK;
}

int ReadFrameYuv(int camera_id, Output* buffer){
	ASC_LOG_INFO("ReadFrameYuv");
	int ret = ReadFrameFromCamera(camera_id, (void*)(buffer->data), (int *)&(buffer->size));
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Get image from camera %d failed", camera_id);
		return STATUS_ERROR;
	}

	return STATUS_OK;	
}

int ReadFrameJpeg(int camera_id, Output* buffer){
	g_camera_mgr.yuv_image_buf->image_size = g_camera_mgr.yuv_image_buf->buf_size;
	ASC_LOG_INFO("ReadFrameJpeg, yuv buf 0x%x, size %d", 
	             g_camera_mgr.yuv_image_buf->data, g_camera_mgr.yuv_image_buf->image_size);
	int ret = ReadFrameFromCamera(camera_id, (void*)(g_camera_mgr.yuv_image_buf->data), 
	                              (int *)&(g_camera_mgr.yuv_image_buf->image_size));
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Get image from camera %d failed", camera_id);
		return STATUS_ERROR;
	}
    ASC_LOG_INFO("Read image success, now convert to jpeg");
	ret = Yuv2Jpeg(buffer, g_camera_mgr.yuv_image_buf);
	if (ret != STATUS_OK) {
		ASC_LOG_ERROR("Convert image to jpeg failed");
	}

	return ret;
}

int ReadFrameRgb(int camera_id, Output* buffer){
	ASC_LOG_INFO("ReadFrameRgb");
	int ret = ReadFrameJpeg(camera_id, buffer);
	if (ret != STATUS_OK) {
		ASC_LOG_ERROR("Read frame of format rgb failed for get jpg image error");
		return ret;
	}

    ret = Jpeg2Rgb(buffer, buffer);
	if (ret != STATUS_OK){
		ASC_LOG_ERROR("Read frame of format rgb failed for jpg convert to rgb error");
	}
    
	return ret;	
}

int Read(int camera_id, Output* buffer){
	ASC_LOG_INFO("Read image from camera %d, buffer 0x%x size %d", camera_id, buffer->data, buffer->size);
	switch (g_camera_mgr.config.format){
		case CAMERA_IMAGE_FORMAT_YUV420:
			return ReadFrameYuv(camera_id, buffer);
		case CAMERA_IMAGE_FORMAT_JPEG:
		    return ReadFrameJpeg(camera_id, buffer);
		case CAMERA_IMAGE_FORMAT_RGB:
		    return ReadFrameRgb(camera_id, buffer);
		default:
		    ASC_LOG_ERROR("Read frame failed for amera image format %d is invalid",
			              g_camera_mgr.config.format);
	}

	return STATUS_ERROR;
}

int Close(int camera_id) {
	int ret = CloseCamera(camera_id);
	if (ret == LIBMEDIA_STATUS_FAILED) {
		ASC_LOG_ERROR("Close camera %d failed", camera_id);
		return STATUS_ERROR;
	}

	return STATUS_OK;
}


}
