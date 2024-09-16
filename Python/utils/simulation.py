import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from Python.utils.application import ApplicationClass
from Python.utils.constant import PRIVACY_INDEX_D, OUTPUTS_PATH_S
from Python.utils.enum import AppTypeEnum
from Python.utils.miscellaneous import read_json


def read_appinfos(dir_s: str):
    filenames_d: dict = {
        "SmartThings": AppTypeEnum.SMARTTHINGS,
        "IFTTT": AppTypeEnum.IFTTT,
        "OpenHAB": AppTypeEnum.OPENHAB,
    }
    applications_l: list = []
    fat_applications_l: list = []
    total_apps_d: dict = {}
    fat_apps_d: dict = {}
    empty_apps_d: dict = {}
    clean_apps_d: dict = {}
    used_apps_d: dict = {}
    clean_apps_i = 0
    used_apps_i = 0
    for filename_s, filetype_s in filenames_d.items():
        path_s = f"{dir_s}/{filename_s}.json"
        if not os.path.exists(path_s):
            continue
        apps_d: dict = read_json(path_s)
        total_apps_d[filetype_s] = len(apps_d)

        for appname_s, detail_d in apps_d.items():
            application_u: ApplicationClass = ApplicationClass(
                appname_s, detail_d, filetype_s
            )
            if application_u.isfat:
                fat_apps_d[filetype_s] = fat_apps_d.get(filetype_s, 0) + 1
                fat_applications_l.append(application_u)
            elif application_u.isempty:
                empty_apps_d[filetype_s] = empty_apps_d.get(filetype_s, 0) + 1
            else:
                clean_apps_d[filetype_s] = clean_apps_d.get(filetype_s, 0) + 1
            applications_l.append(application_u)
    for filetype_s, number_i in clean_apps_d.items():
        used_apps_d[filetype_s] = number_i + fat_apps_d.get(filetype_s, 0)
        clean_apps_i += number_i
        used_apps_i += used_apps_d[filetype_s]
    return (
        applications_l,
        fat_applications_l,
        total_apps_d,
        fat_apps_d,
        empty_apps_d,
        clean_apps_d,
        used_apps_d,
        clean_apps_i,
        used_apps_i,
    )


def get_application_by_name(applications_l, name_s):
    for application_u in applications_l:
        if application_u.appname == name_s:
            return application_u
    return None


def get_device_related_appinfos(
    app_info_l: list[ApplicationClass], fat_include_b=False, empty_include_b=False
):
    device_application_d: dict = {}
    for application_u in app_info_l:
        if application_u.isfat and (not fat_include_b):
            continue
        if application_u.isempty and (not empty_include_b):
            continue
        devices_e = application_u.devsets
        for device_s in devices_e:
            if device_s not in device_application_d:
                device_application_d[device_s] = []
            device_application_d[device_s].append(application_u)
    return device_application_d


def update_sensitive_devices_of_privacy_label(
    rand_sensitive_devices_d, privacy_type_d, threat_type_m
):
    for chainlists_u, inference_d in privacy_type_d.items():
        for state_s, inference_u in inference_d.items():
            for privacy_label_s in inference_u.privacy:
                threat_privacy_d = rand_sensitive_devices_d[threat_type_m][
                    privacy_label_s
                ]
                threat_privacy_d[inference_u.device] = (
                    threat_privacy_d.get(inference_u.device, 0) + 1
                )


def convert_sensitive_devices_based_on_frequency(rand_sensitive_devices_d):
    sensitive_devices_d = {
        threat_type_m: {priv_label_s: {} for priv_label_s in PRIVACY_INDEX_D}
        for threat_type_m in rand_sensitive_devices_d
    }
    for threat_type_m, privacy_type_d in rand_sensitive_devices_d.items():
        for privacy_type_s in privacy_type_d:
            sensitive_devices_d[threat_type_m][privacy_type_s] = sorted(
                privacy_type_d[privacy_type_s].items(), key=lambda x: (-x[1], x[0])
            )
    return sensitive_devices_d


def get_count_of_privacy_types(privacy_type_d):
    num_labels_i = len(PRIVACY_INDEX_D)
    privacy_types_l = np.zeros(num_labels_i)

    visited_l = []

    for chainlists_u, inference_d in privacy_type_d.items():
        for state_s, inference_u in inference_d.items():
            if inference_u.device in visited_l:
                continue
            visited_l.append(inference_u.device)

            for privacy_label_s in inference_u.privacy:
                privacy_types_l[PRIVACY_INDEX_D[privacy_label_s]] += 1
    return privacy_types_l


def plot_count_length(num_dev_l, mean_count_length_l, index_i=0):

    markersize = 12
    linewidth = 2
    fontsize = 13
    labelsize = 13

    position_i = mean_count_length_l.shape[-2]

    # count
    count_wo_l = mean_count_length_l[index_i, 0, 0, :]
    count_w_l = mean_count_length_l[index_i, 1, 0, :]
    # avg_len
    avg_len_wo_l = mean_count_length_l[index_i, 0, position_i - 2, :]
    avg_len_w_l = mean_count_length_l[index_i, 1, position_i - 2, :]
    # max_len
    max_len_wo_l = mean_count_length_l[index_i, 0, position_i - 1, :]
    max_len_w_l = mean_count_length_l[index_i, 1, position_i - 1, :]

    # Create figure and subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Number of Chains
    ax1.plot(
        num_dev_l,
        count_wo_l,
        label="num wo/fat",
        marker="s",
        linestyle="-",
        color="r",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax1.plot(
        num_dev_l,
        count_w_l,
        label="num w/fat",
        marker="s",
        linestyle="--",
        color="b",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax1.set_title("(a)", fontsize=fontsize)
    ax1.set_ylabel("Number", fontsize=fontsize)
    ax1.legend()
    ax1.tick_params(axis="x", which="major", labelsize=labelsize)
    ax1.tick_params(axis="y", which="major", labelsize=labelsize)

    # Avg Length, Max Length
    ax2.plot(
        num_dev_l,
        avg_len_wo_l,
        label="avg(len) wo/fat",
        marker="o",
        linestyle="-",
        color="r",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax2.plot(
        num_dev_l,
        avg_len_w_l,
        label="avg(len) w/fat",
        marker="o",
        linestyle="--",
        color="b",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax2.plot(
        num_dev_l,
        max_len_wo_l,
        label="max(len) wo/fat",
        marker="^",
        linestyle="-",
        color="r",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax2.plot(
        num_dev_l,
        max_len_w_l,
        label="max(len) w/fat",
        marker="^",
        linestyle="--",
        color="b",
        markersize=markersize,
        linewidth=linewidth,
    )
    ax2.set_title("(b)", fontsize=fontsize)
    ax2.set_ylabel("Length", fontsize=fontsize)
    ax2.legend()
    # ax2.tick_params(axis="x", which="major", labelsize=labelsize)
    # ax2.tick_params(axis="y", which="major", labelsize=labelsize)
    ax2.tick_params(axis="both", which="both", labelsize=labelsize)

    fig.text(0.5, 0.05, "# Apps", fontsize=fontsize, ha="center")

    # plt.tight_layout()
    # plt.savefig(f"{OUTPUTS_PATH_S}/figure6-{index_i}.pdf", bbox_inches="tight")
    plt.savefig(f"{OUTPUTS_PATH_S}/figure6.pdf", bbox_inches="tight")
    # plt.show()


def plot_grouped_bar(ax, num_dev_l, privacy_type_l, title_s, ylim_f=15):
    fontsize = 13
    labelsize = 13

    labels_l = list(PRIVACY_INDEX_D.keys())
    num_labels_i = len(labels_l)
    total_width_f = 0.85
    bar_width_f = total_width_f / num_labels_i
    num_dev_i = len(num_dev_l)
    ticks_dev_l = list(map(str, num_dev_l))
    # yticks_l = range(int(np.ceil(ylim_f)))

    for idx_i in range(num_labels_i):
        label_s = labels_l[idx_i]
        ax.bar(
            [idx_j + idx_i * bar_width_f for idx_j in range(num_dev_i)],
            height=privacy_type_l[idx_i, :],
            label=label_s,
            width=bar_width_f,
        )

    ax.set_xticks(
        [idx_j + bar_width_f / 2 * (num_labels_i - 1) for idx_j in range(num_dev_i)],
        ticks_dev_l,
    )
    # ax.set_yticks(yticks_l)

    # ax.tick_params(axis="x", which="major", labelsize=labelsize)
    # ax.tick_params(axis="y", which="major", labelsize=labelsize)
    ax.tick_params(axis="both", which="both", labelsize=labelsize)
    ax.set_title(title_s, fontsize=fontsize)
    ax.set_ylim(0, ylim_f)


def plot_stacked_bar(ax, num_dev_l, privacy_type_l, title_s, ylim_f=15):
    fontsize = 13
    labelsize = 13

    labels_l = list(PRIVACY_INDEX_D.keys())
    num_labels_i = len(labels_l)
    num_dev_l = list(map(str, num_dev_l))
    # yticks_l = range(int(np.ceil(ylim_f)))

    for idx_i in range(num_labels_i):
        label_s = labels_l[idx_i]
        if idx_i == 0:
            ax.bar(num_dev_l, privacy_type_l[idx_i, :], label=label_s)
        else:
            bottom_l = np.sum(privacy_type_l[:idx_i, :], 0)
            ax.bar(
                num_dev_l,
                privacy_type_l[idx_i, :],
                bottom=bottom_l,
                label=label_s,
            )

    # ax.set_yticks(yticks_l)
    # ax.tick_params(axis="x", which="major", labelsize=labelsize)
    # ax.tick_params(axis="y", which="major", labelsize=labelsize)
    ax.tick_params(axis="both", which="both", labelsize=labelsize)
    ax.set_title(title_s, fontsize=fontsize)
    ax.set_ylim(0, ylim_f)


def plot_grouped_and_stacked_bar(num_dev_l, mean_privacy_types_l):

    fontsize = 13
    redundancy_f = 0.1

    # 0 2: include chain=1 or not
    # 1 2: wo/w fat apps
    # 2 3: count, avg_len, max_len
    # 3 len_num_priv_i: number of privacy types
    # 4 len_num_dev_i: number of devices

    direct_exposure_wo_fat_l = mean_privacy_types_l[1, 0, 0, :, :]
    implicit_inference_wo_fat_l = mean_privacy_types_l[1, 0, 1, :, :]
    # multiple_inference_wo_fat_l = mean_privacy_types_l[1, 0, 2, :, :]
    direct_exposure_w_fat_l = mean_privacy_types_l[1, 1, 0, :, :]
    implicit_inference_w_fat_l = mean_privacy_types_l[1, 1, 1, :, :]
    # multiple_inference_w_fat_l = mean_privacy_types_l[1, 1, 2, :, :]

    direct_exposure_wo_fat_w_sink_l = mean_privacy_types_l[0, 0, 0, :, :]
    implicit_inference_wo_fat_w_sink_l = mean_privacy_types_l[0, 0, 1, :, :]
    multiple_inference_wo_fat_w_sink_l = mean_privacy_types_l[0, 0, 2, :, :]
    direct_exposure_w_fat_w_sink_l = mean_privacy_types_l[0, 1, 0, :, :]
    implicit_inference_w_fat_w_sink_l = mean_privacy_types_l[0, 1, 1, :, :]
    multiple_inference_w_fat_w_sink_l = mean_privacy_types_l[0, 1, 2, :, :]

    labels_l = list(PRIVACY_INDEX_D.keys())
    fig, axs = plt.subplots(2, 5)
    # plt.subplots_adjust(wspace=0.5)

    for i in range(5):
        axs[0, i].set_position([-1 + 0.59 * i + 0.05 * (i // 2), 0.65, 0.5, 0.4])
        axs[1, i].set_position([-1 + 0.59 * i + 0.05 * (i // 2), 0.13, 0.5, 0.4])

    max_direct_exposure_f = get_max_ylim(
        direct_exposure_wo_fat_l, direct_exposure_w_fat_l, redundancy_f, "Grouped"
    )
    ax = axs[0, 0]
    plot_grouped_bar(
        ax, num_dev_l, direct_exposure_wo_fat_l, "(a)", max_direct_exposure_f
    )
    ax = axs[1, 0]
    plot_grouped_bar(
        ax, num_dev_l, direct_exposure_w_fat_l, "(b)", max_direct_exposure_f
    )

    max_direct_exposure_w_sink_f = get_max_ylim(
        direct_exposure_wo_fat_w_sink_l,
        direct_exposure_w_fat_w_sink_l,
        redundancy_f,
        "Stacked",
    )
    ax = axs[0, 1]
    plot_stacked_bar(
        ax,
        num_dev_l,
        direct_exposure_wo_fat_w_sink_l,
        "(c)",
        max_direct_exposure_w_sink_f,
    )
    ax = axs[1, 1]
    plot_stacked_bar(
        ax,
        num_dev_l,
        direct_exposure_w_fat_w_sink_l,
        "(d)",
        max_direct_exposure_w_sink_f,
    )

    rect1 = patches.Rectangle(
        (-1.07, 0.065),
        1.18,
        1.04,
        linewidth=2,
        edgecolor="black",
        linestyle="--",
        facecolor="none",
        transform=fig.transFigure,
    )

    max_implicit_inference_f = get_max_ylim(
        implicit_inference_wo_fat_l, implicit_inference_w_fat_l, redundancy_f, "Grouped"
    )
    ax = axs[0, 2]
    plot_grouped_bar(
        ax, num_dev_l, implicit_inference_wo_fat_l, "(e)", max_implicit_inference_f
    )
    ax = axs[1, 2]
    plot_grouped_bar(
        ax, num_dev_l, implicit_inference_w_fat_l, "(f)", max_implicit_inference_f
    )

    max_implicit_inference_w_sink_f = get_max_ylim(
        implicit_inference_wo_fat_w_sink_l,
        implicit_inference_w_fat_w_sink_l,
        redundancy_f,
        "Stacked",
    )
    ax = axs[0, 3]
    plot_stacked_bar(
        ax,
        num_dev_l,
        implicit_inference_wo_fat_w_sink_l,
        "(g)",
        max_implicit_inference_w_sink_f,
    )
    ax = axs[1, 3]
    plot_stacked_bar(
        ax,
        num_dev_l,
        implicit_inference_w_fat_w_sink_l,
        "(h)",
        max_implicit_inference_w_sink_f,
    )

    rect2 = patches.Rectangle(
        (0.16, 0.065),
        1.18,
        1.04,
        linewidth=2,
        edgecolor="black",
        linestyle="--",
        facecolor="none",
        transform=fig.transFigure,
    )

    max_multiple_inference_w_sink_f = get_max_ylim(
        multiple_inference_wo_fat_w_sink_l,
        multiple_inference_w_fat_w_sink_l,
        redundancy_f,
        "Grouped",
    )
    ax = axs[0, 4]
    plot_grouped_bar(
        ax,
        num_dev_l,
        multiple_inference_wo_fat_w_sink_l,
        "(i)",
        max_multiple_inference_w_sink_f,
    )
    ax = axs[1, 4]
    plot_grouped_bar(
        ax,
        num_dev_l,
        multiple_inference_w_fat_w_sink_l,
        "(j)",
        max_multiple_inference_w_sink_f,
    )

    rect3 = patches.Rectangle(
        (1.39, 0.065),
        0.59,
        1.04,
        linewidth=2,
        edgecolor="black",
        linestyle="--",
        facecolor="none",
        transform=fig.transFigure,
    )

    # plt.figlegend(
    #     labels_l, fontsize=fontsize, loc="lower center", ncol=6, labelspacing=0
    # )
    plt.figlegend(
        labels_l,
        fontsize=fontsize,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.07),
        ncol=6,
        labelspacing=0,
    )
    # plt.show()
    fig.text(0.5, 0.03, "# Apps", fontsize=fontsize, ha="center")
    fig.text(
        -1.099, 0.583, "Number", fontsize=fontsize, va="center", rotation="vertical"
    )

    fig.patches.append(rect1)
    fig.patches.append(rect2)
    fig.patches.append(rect3)

    plt.savefig(f"{OUTPUTS_PATH_S}/figure7.pdf", bbox_inches="tight")
    # plt.show()
    plt.close()


def get_max_ylim(first_l, second_l, redundancy_f, type_s="Stacked"):
    max_first_f = np.max(first_l)
    max_second_f = np.max(second_l)
    if type_s == "Stacked":
        max_first_f = np.max(np.sum(first_l, 0))
        max_second_f = np.max(np.sum(second_l, 0))

    max_f = max(max_first_f, max_second_f) * (1 + redundancy_f)
    return max_f


def get_top_ratio_results(results_l, ratio_f=0.8, num_i=5):
    if len(results_l) < num_i:
        return [device_s for device_s, frequency_i in results_l]
    devices_l = []
    total_i = sum([frequency_i for device_s, frequency_i in results_l])
    cutoff_f = total_i * ratio_f

    current_i = 0
    for device_s, frequency_i in results_l:
        if current_i >= cutoff_f:
            break
        devices_l.append(device_s)
        current_i += frequency_i
    return devices_l
