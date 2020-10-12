import torch
# import torch.nn as nn
# import torch.nn.functional as F
import numpy as np


HUGE_NUMBER = 1e10
TINY_NUMBER = 1e-6      # float32 only has 7 decimal digits precision


# Misc utils
# work on tensors
# img2mse = lambda x, y: torch.mean((x - y) * (x - y))
def img2mse(x, y, mask=None):
    if mask is None:
        return torch.mean((x - y) * (x - y))
    else:
        return torch.sum((x - y) * (x - y) * mask.unsqueeze(-1)) / (torch.sum(mask) * x.shape[-1] + TINY_NUMBER)

img_HWC2CHW = lambda x: x.permute(2, 0, 1)
gray2rgb = lambda x: x.unsqueeze(2).repeat(1, 1, 3)


def normalize(x):
    min = x.min()
    max = x.max()

    return (x - min) / ((max - min) + TINY_NUMBER)


to8b = lambda x: (255 * np.clip(x, 0, 1)).astype(np.uint8)
# gray2rgb = lambda x: np.tile(x[:,:,np.newaxis], (1, 1, 3))
mse2psnr = lambda x: -10. * np.log(x+TINY_NUMBER) / np.log(10.)

#
# def normalize(x):
#     x_min, x_max = np.percentile(x, (0.5, 99.5))
#     x = np.clip(x, x_min, x_max)
#     x = (x - x_min) / (x_max - x_min)
#     return x


########################################################################################################################
#
########################################################################################################################
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import matplotlib as mpl
from matplotlib import cm
import cv2


def get_vertical_colorbar(h, vmin, vmax, cmap_name='jet', label=None):
    '''
    :param w: pixels
    :param h: pixels
    :param vmin: min value
    :param vmax: max value
    :param cmap_name:
    :param label
    :return:
    '''
    fig = Figure(figsize=(1.2, 8), dpi=100)
    fig.subplots_adjust(right=1.5)
    canvas = FigureCanvasAgg(fig)

    # Do some plotting.
    ax = fig.add_subplot(111)
    cmap = cm.get_cmap(cmap_name)
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    tick_cnt = 6
    tick_loc = np.linspace(vmin, vmax, tick_cnt)
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                    norm=norm,
                                    ticks=tick_loc,
                                    orientation='vertical')

    tick_label = ['{:3.2f}'.format(x) for x in tick_loc]
    cb1.set_ticklabels(tick_label)

    cb1.ax.tick_params(labelsize=18, rotation=0)

    if label is not None:
        cb1.set_label(label)

    fig.tight_layout()

    # # debug
    # fig.savefig("debug3.png")

    canvas.draw()
    s, (width, height) = canvas.print_to_buffer()

    im = np.frombuffer(s, np.uint8).reshape((height, width, 4))

    im = im[:, :, :3].astype(np.float32) / 255.
    if h != im.shape[0]:
        w = int(im.shape[1] / im.shape[0] * h)
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)

    return im


# def colorize_np(x, cmap_name='jet', append_cbar=False):
#     vmin = x.min()
#     vmax = x.max() + TINY_NUMBER
#     x = (x - vmin) / (vmax - vmin)
#     # x = np.clip(x, 0., 1.)

#     cmap = cm.get_cmap(cmap_name)
#     x_new = cmap(x)[:, :, :3]

#     cbar = get_vertical_colorbar(h=x.shape[0], vmin=vmin, vmax=vmax, cmap_name=cmap_name)

#     if append_cbar:
#         x_new = np.concatenate((x_new, np.zeros_like(x_new[:, :5, :]), cbar), axis=1)
#         return x_new
#     else:
#         return x_new, cbar


# # tensor
# def colorize(x, cmap_name='jet', append_cbar=False):
#     x = x.numpy()
#     x, cbar = colorize_np(x, cmap_name)

#     if append_cbar:
#         x = np.concatenate((x, np.zeros_like(x[:, :5, :]), cbar), axis=1)

#     x = torch.from_numpy(x)
#     return x

def colorize_np(x, cmap_name='jet', mask=None, append_cbar=False):
    if mask is not None:
        # vmin, vmax = np.percentile(x[mask], (1, 99))
        vmin = np.min(x[mask])
        vmax = np.max(x[mask])
        vmin = vmin - np.abs(vmin) * 0.01
        x[np.logical_not(mask)] = vmin
        x = np.clip(x, vmin, vmax)
        # print(vmin, vmax)
    else:
        vmin = x.min()
        vmax = x.max() + TINY_NUMBER

    x = (x - vmin) / (vmax - vmin)
    # x = np.clip(x, 0., 1.)

    cmap = cm.get_cmap(cmap_name)
    x_new = cmap(x)[:, :, :3]

    if mask is not None:
        mask = np.float32(mask[:, :, np.newaxis])
        x_new = x_new * mask + np.zeros_like(x_new) * (1. - mask)

    cbar = get_vertical_colorbar(h=x.shape[0], vmin=vmin, vmax=vmax, cmap_name=cmap_name)

    if append_cbar:
        x_new = np.concatenate((x_new, np.zeros_like(x_new[:, :5, :]), cbar), axis=1)
        return x_new
    else:
        return x_new, cbar


# tensor
def colorize(x, cmap_name='jet', append_cbar=False, mask=None):
    x = x.numpy()
    if mask is not None:
        mask = mask.numpy().astype(dtype=np.bool)
    x, cbar = colorize_np(x, cmap_name, mask)

    if append_cbar:
        x = np.concatenate((x, np.zeros_like(x[:, :5, :]), cbar), axis=1)

    x = torch.from_numpy(x)
    return x


if __name__ == '__main__':
    # # cbar = get_vertical_colorbar(h=512, vmin=0.1, vmax=5, cmap_name='jet')
    # # cbar = cbar[:, :, :3]
    # import imageio
    #
    # # imageio.imwrite('./debug.png', cbar)
    #
    # x = torch.rand(512, 512)
    # x = colorize(x, append_cbar=True)
    #
    # x = np.uint8(x.numpy() * 255.)
    #
    # import imageio
    # imageio.imwrite('./debug.png', x)

    import os
    import imageio

    img_dir = '/phoenix/S7/kz298/latest_work/nerf/logs/dtu_scan9_3_nearfar/renderonly_train_200001'

    all_imgs = []
    for item in sorted(os.listdir(img_dir)):
        if item[-4:] == '.png':
            fpath = os.path.join(img_dir, item)
            all_imgs.append(imageio.imread(fpath))

    imageio.mimwrite(os.path.join(img_dir, 'video.mp4'), all_imgs, fps=3, quality=8)