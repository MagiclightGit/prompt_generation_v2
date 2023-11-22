'''
Description: API for image editor
Author: guoping
Date: 2023-06-07 19:30:15
Acknowledgements: TBD
'''

import os
import zipfile

import cv2
import numpy as np


class ImageEditor(object):
    @staticmethod
    def fill_image_to_square(img):
        h, w = img.shape[:2]
        out_size = max(h, w)
        top = (out_size - h) // 2
        bottom = (out_size - h) - top
        left = (out_size - w) // 2
        right = (out_size - w) - left
        kernel_size = out_size // 12 * 2 + 1

        mask = np.zeros((out_size, out_size))
        mask[top : out_size - bottom, left : out_size - right] = np.ones((h, w))
        mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), sigmaX=32, sigmaY=32)
        mask = np.stack([mask, mask, mask], axis=2)

        base_image = np.ones((out_size, out_size, 3)) * 255
        padding_color = np.average(img[:64, :64, :], axis=(0, 1))
        image = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=tuple(padding_color))
        image = (1 - mask) * base_image + mask * image
        return image.astype(np.uint8)

    @staticmethod
    def zip_dir(process_dir, zip_path):
        dir_name = os.path.basename(process_dir)
        with zipfile.ZipFile(zip_path, 'w') as f:
            for file_name in os.listdir(process_dir):
                f.write(f'{process_dir}/{file_name}', f'{dir_name}/{file_name}')

    @staticmethod
    def interp(imgs, num=9):
        frames = list()
        for i in range(len(imgs) - 1):
            img1, img2 = imgs[i].astype(np.float32), imgs[i + 1].astype(np.float32)
            frames.append(img1.astype(np.uint8))
            img_diff = img2 - img1
            for j in np.linspace(0, 1, num + 2)[1:-1]:
                img_int = np.round(img1 + img_diff * j)
                frames.append(img_int.astype(np.uint8))
        frames.append(imgs[-1])
        return frames

    @staticmethod
    def add_alpha(img_path, out_path, alpha=255):
        img = cv2.imread(img_path)
        alpha = np.ones(img.shape[:2], dtype=np.uint8) * alpha
        img_alpha = cv2.merge([img, alpha])
        cv2.imwrite(out_path, img_alpha)

    @staticmethod
    def get_img_size(img_url):
        succ, img = cv2.VideoCapture(img_url).read()
        if succ:
            height, width = img.shape[:2]
            return height, width
        else:
            raise ValueError(f'Invalid image url: {img_url}')
