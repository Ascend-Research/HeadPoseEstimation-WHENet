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

#include "opencv2/opencv.hpp"
#include "opencv2/imgcodecs/legacy/constants_c.h"
#include "dvpp_image.h"
#include "log.h"

using namespace std;

extern "C" {

DvppConfig dvppConfig;

ImageBuffer::ImageBuffer(uint32_t _width, uint32_t _height):
                        width(_width), height(_height), image_size(0) {
	uint32_t stride = ALIGN_UP(_width, ALIGN_16);
	buf_size = ALIGN_UP(YUV420SP_SIZE(stride, _height), PAGE_SIZE);
	raw_data = new (nothrow) uint8_t[buf_size + JPEG_ENCODE_ADDR_ALIGN];
    data = (unsigned char*) ALIGN_UP((uint64_t)raw_data, JPEG_ENCODE_ADDR_ALIGN);                                 
}

ImageBuffer::~ImageBuffer(){
	delete[] data;
}

void InitDvpp(uint32_t width, uint32_t height) {
	dvppConfig.width = width;
	dvppConfig.height = height;
	dvppConfig.yuv_image = new ImageBuffer(width, height);
	dvppConfig.yuv_image->width = width;
	dvppConfig.yuv_image->height = height;
	dvppConfig.yuv_image->image_size = width * height * 3 /2;
	return;
}

void CvtYuv2Jpeg(Output* output_jpeg, uint8_t* data) {
	output_jpeg->size = dvppConfig.width * dvppConfig.height * 3;
	memcpy_s(dvppConfig.yuv_image->data, dvppConfig.yuv_image->image_size, data, dvppConfig.yuv_image->image_size);
    Yuv2Jpeg(output_jpeg, dvppConfig.yuv_image);
    return;
}

int Yuv2Jpeg(Output* output_jpeg, ImageBuffer* yuv_image) {
	sJpegeIn input_data;
	// yuv image width/height/encoding quality level(1-100)/format/height
	input_data.width = CHECK_EVEN(yuv_image->width);
	input_data.height = CHECK_EVEN(yuv_image->height);
	input_data.level = 100;
	input_data.format = yuv_image->format;
	input_data.heightAligned = yuv_image->height;
	// align width to 16
	input_data.stride = ALIGN_UP(input_data.width, ALIGN_16);
	input_data.bufSize = ALIGN_UP(YUV420SP_SIZE(input_data.stride, input_data.heightAligned), PAGE_SIZE);
	input_data.buf = yuv_image->data;

	sJpegeOut output_data;
	dvppapi_ctl_msg dvpp_ctl_msg;
	dvpp_ctl_msg.in = static_cast<void*>(&input_data);
	dvpp_ctl_msg.in_size = sizeof(sJpegeIn);
	dvpp_ctl_msg.out = static_cast<void*>(&output_data);
	dvpp_ctl_msg.out_size = sizeof(sJpegeOut);
	IDVPPAPI* pidvppapi = NULL;
	CreateDvppApi(pidvppapi);
	if (pidvppapi == NULL) {
		ASC_LOG_ERROR("Can not open dvppapi engine");
		return STATUS_ERROR;
	}
	if (0 != DvppCtl(pidvppapi, DVPP_CTL_JPEGE_PROC, &dvpp_ctl_msg)) {
		DestroyDvppApi(pidvppapi);
		ASC_LOG_ERROR("Dvpp process error");
		return STATUS_ERROR;
	}

	int ret = memcpy_s(output_jpeg->data, output_jpeg->size, output_data.jpgData, output_data.jpgSize);
	if (ret != EOK) {
		ASC_LOG_ERROR("memcpy_s return %d, src jpeg size %d, dest out buffer size %d",
			ret, output_data.jpgSize, output_jpeg->size);
		ret = STATUS_ERROR;
	}
	else {
		output_jpeg->size = output_data.jpgSize;
		ret = STATUS_OK;
	}

	output_data.cbFree();
	DestroyDvppApi(pidvppapi);
    ASC_LOG_INFO("Conver jpeg return %d", ret);
	return ret;
}

int Jpeg2Rgb(Output* dest_rgb, Output* src_jpeg){
	cv::_InputArray pic_arr(src_jpeg->data, src_jpeg->size);
	cv::Mat img_mat = cv::imdecode(pic_arr, CV_LOAD_IMAGE_COLOR);
	int ret = memcpy_s(dest_rgb->data, dest_rgb->size, img_mat.ptr<u_int8_t>(),
							img_mat.total() * img_mat.channels());
	if (ret != EOK){
		ASC_LOG_ERROR("Decode jpeg failed");
		ret = STATUS_ERROR;
	}
	dest_rgb->size = img_mat.total() * img_mat.channels();

	return ret;
}

void DataWrite(char* filename, uint8_t* data, int size)
{
	FILE *fid;
	
	fid = fopen(filename,"wb");
	if(fid == NULL)
	{
		ASC_LOG_ERROR("Write file error");
		return;
	}	
	fwrite(data, sizeof(uint8_t), size, fid);
	fclose(fid);
}
}
