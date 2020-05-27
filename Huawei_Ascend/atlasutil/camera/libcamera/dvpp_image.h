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

#ifndef _DVPP_IMAGE_H_
#define _DVPP_IMAGE_H_
#include "securec.h"
#include "dvpp/idvppapi.h"
#include "dvpp/Jpeg.h"

extern "C" {

#define CHECK_ODD(NUM) (((NUM) % 2 != 0) ? (NUM) : ((NUM) - 1))
#define CHECK_EVEN(NUM) (((NUM) % 2 == 0) ? (NUM) : ((NUM) - 1))

#define YUV420SP_SIZE(width, height) (width * height * 3 / 2)
#define ALIGN_16     (16)
#define JPEG_ENCODE_ADDR_ALIGN   (128)

struct Output {
	uint32_t size;
	uint8_t* data;
};

struct YuvBuffer
{
	eEncodeFormat format = JPGENC_FORMAT_NV12;
	uint32_t buf_size;
	uint32_t width;
	uint32_t height;
	uint32_t imgage_size;
	uint8_t* data;
};


class ImageBuffer {
public:
    ImageBuffer(uint32_t width, uint32_t height);
	~ImageBuffer();
public:
	eEncodeFormat format = JPGENC_FORMAT_NV12;
	uint32_t buf_size;
	uint32_t width;
	uint32_t height;
	uint32_t image_size;
	uint8_t* data;

private:
    uint8_t* raw_data;
};

struct DvppConfig
{
	uint32_t width;
	uint32_t height;
	ImageBuffer* yuv_image;
};

int Jpeg2Rgb(Output* dest_rgb, Output* src_jpeg);
void InitDvpp(uint32_t width, uint32_t height);
void CvtYuv2Jpeg(Output* output_jpeg, uint8_t* data);
int Yuv2Jpeg(Output* output_jpeg, ImageBuffer* yuv_image);
void DataWrite(char* filename, uint8_t* data, int size);
}

#endif
