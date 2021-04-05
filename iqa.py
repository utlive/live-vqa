from .utils import compute_image_mscn_transform, extract_subband_feats, moments
import cv2
import numpy as np


# TODO: Compare with Matlab
def brisque(image):
    y_mscn = compute_image_mscn_transform(image)
    half_scale = cv2.resize(image, dsize=(0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LANCZOS4)
    y_half_mscn = compute_image_mscn_transform(half_scale)
    feats_full = extract_subband_feats(y_mscn)
    feats_half = extract_subband_feats(y_half_mscn)
    return np.concatenate((feats_full, feats_half))


def ssim(img_ref, img_dist, k=11, max_val=1, K1=0.01, K2=0.03, no_lum=False, full=False, padding=None, stride=1):
    x = img_ref.astype('float32')
    y = img_dist.astype('float32')
    mu_x, mu_y, var_x, var_y, cov_xy = moments(x, y, k, stride, padding=padding)

    C1 = (max_val*K1)**2
    C2 = (max_val*K2)**2

    if not no_lum:
        l = (2*mu_x*mu_y + C1)/(mu_x**2 + mu_y**2 + C1)
    cs = (2*cov_xy + C2)/(var_x + var_y + C2)

    ssim_map = cs
    if not no_lum:
        ssim_map *= l

    if (full):
        return (np.mean(ssim_map), ssim_map)
    else:
        return np.mean(ssim_map)


def ms_ssim(img_ref, img_dist, k=11, max_val=1, K1=0.01, K2=0.03, full=False, padding=None, stride=1):
    x = img_ref.astype('float32')
    y = img_dist.astype('float32')

    n_levels = 5
    weights = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333])
    scores = np.ones((n_levels,))
    for i in range(n_levels-1):
        if np.min(x.shape) <= k:
            break
        scores[i] = ssim(x, y, k, max_val, K1, K2, no_lum=True, padding=padding, stride=stride)
        x = x[:(x.shape[0]//2)*2, :(x.shape[1]//2)*2]
        y = y[:(y.shape[0]//2)*2, :(y.shape[1]//2)*2]
        x = (x[::2, ::2] + x[1::2, ::2] + x[1::2, 1::2] + x[::2, 1::2])/4
        y = (y[::2, ::2] + y[1::2, ::2] + y[1::2, 1::2] + y[::2, 1::2])/4

    if np.min(x.shape) > k:
        scores[-1] = ssim(x, y, k, max_val, K1, K2, no_lum=False, padding=padding, stride=stride)
    msssim = np.prod(np.power(scores, weights))
    if full:
        return msssim, scores
    else:
        return msssim


def vif_spatial(img_ref, img_dist, k=11, max_val=1, sigma_nsq=0.1, padding=None):
    x = img_ref.astype('float32')
    y = img_dist.astype('float32')

    _, _, var_x, var_y, cov_xy = moments(x, y, k, 1)

    g = cov_xy / (var_x + 1e-10)
    sv_sq = var_y - g * cov_xy

    g[var_x < 1e-10] = 0
    sv_sq[var_x < 1e-10] = var_y[var_x < 1e-10]
    var_x[var_x < 1e-10] = 0

    g[var_y < 1e-10] = 0
    sv_sq[var_y < 1e-10] = 0

    sv_sq[g < 0] = var_x[g < 0]
    g[g < 0] = 0
    sv_sq[sv_sq < 1e-10] = 1e-10

    vif_val = np.sum(np.log(1 + g**2 * var_x / (sv_sq + sigma_nsq)) + 1e-4)/np.sum(np.log(1 + var_x / sigma_nsq) + 1e-4)
    return vif_val
