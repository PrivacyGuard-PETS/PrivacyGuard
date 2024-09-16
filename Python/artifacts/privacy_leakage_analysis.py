import sys
import random

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QTableWidget,
    QMessageBox,
    QSizeGrip,
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import networkx as nx

from Python.utils.constant import (
    CASE_STUDY_APPS_D,
    CASE_STUDY_CASES_D,
    FILES_EXAMPLES_PATH_S,
    PRIVACY_ABBREV_D,
)
from Python.utils.enum import TcaEnum
from Python.utils.miscellaneous import print_memory_usage
from Python.utils.result import MultipleAppChainsClass
from Python.utils.simulation import read_appinfos, get_application_by_name


class MainUI(QWidget):
    def __init__(self, result_u: MultipleAppChainsClass, index_i=0):
        super().__init__()
        self.result = result_u
        self.index = index_i

        self.layout = QVBoxLayout()

        label = QLabel("Input Apps:")
        self.layout.addWidget(label)

        list_widget = QListWidget()
        list_widget.addItems(self.result.appnames)
        self.layout.addWidget(list_widget)

        list_size_grip = QSizeGrip(list_widget)
        self.layout.addWidget(list_size_grip, alignment=Qt.AlignRight | Qt.AlignBottom)
        button = QPushButton("Detect Cross-App Chain")
        button.clicked.connect(self.detect)
        self.layout.addWidget(button)
        # self.layout.addStretch()

        self.setLayout(self.layout)
        self.setWindowTitle("Detect Cross-App Chain")
        self.show()

    def detect(self):
        self.chains_ui = ChainsUI(self.result, self.index)
        self.chains_ui.show()


class ChainsUI(QWidget):
    def __init__(self, result_u: MultipleAppChainsClass, index_i=0):
        super().__init__()

        self.result = result_u
        self.index = index_i

        # self.single_inference = self.result.single_inference[self.index]
        self.single_inference = self.result.single_exists[self.index]
        self.single_chains = list(self.single_inference.keys())

        # self.direct_exposure = self.result.direct_exposure[self.index]
        # self.direct_chains = list(self.direct_exposure.keys())

        # self.implicit_inference = self.result.implicit_inference[self.index]
        # self.implicit_chains = list(self.implicit_inference.keys())

        # self.multiple_inference = self.result.multiple_inference[self.index]
        self.multiple_inference = self.result.multiple_exists[self.index]
        self.multiple_chains = list(self.multiple_inference.keys())

        title_s = "Cross-App Chains with Privacy Risk\n\n"

        self.layout = QHBoxLayout()

        # Single Sink Inference
        single_layout = QVBoxLayout()
        single_label = QLabel()
        single_label = QLabel(title_s + "Single-Sink Inference:")
        single_layout.addWidget(single_label)

        number_single_i, maxlen_single_i = self.get_number_and_max_length(
            self.single_chains
        )
        # self.number_direct_i, self.maxlen_direct_i = self.get_number_and_max_length(
        #     self.direct_chains
        # )
        # self.number_implicit_i, self.maxlen_implicit_i = self.get_number_and_max_length(
        #     self.implicit_chains
        # )
        # number_single_i = self.number_direct_i + self.number_implicit_i
        # maxlen_single_i = max(self.maxlen_direct_i, self.maxlen_implicit_i)

        self.single_tree_widget = QTreeWidget()
        self.single_tree_widget.setHeaderLabels(["Sinks", "Chains"])

        for sink_num_i, chainlist_u in enumerate(self.single_inference):
            number_single_i, maxlen_single_i = (
                chainlist_u.number,
                chainlist_u.max_len[self.index],
            )
            parent_item = QTreeWidgetItem(
                [f"Sink {sink_num_i+1}", f"Chains of Sink {sink_num_i+1}"]
            )
            self.single_tree_widget.addTopLevelItem(parent_item)

            table_widget = QTableWidget(number_single_i, maxlen_single_i)
            table_widget.setHorizontalHeaderLabels(
                [f"App{i_i+1}" for i_i in range(maxlen_single_i)]
            )
            table_height = table_widget.horizontalHeader().height()

            for row_i, chain_u in enumerate(chainlist_u.chains):
                appnames_l: list = chain_u.appnames[::-1]
                for column_i in range(len(appnames_l)):
                    table_widget.setItem(
                        row_i, column_i, QTableWidgetItem(appnames_l[column_i])
                    )
                table_height += table_widget.rowHeight(row_i)
            table_widget.setFixedHeight(table_height)

            table_item = QTreeWidgetItem(parent_item)
            self.single_tree_widget.setItemWidget(table_item, 1, table_widget)

        single_layout.addWidget(self.single_tree_widget)
        single_size_grip = QSizeGrip(self.single_tree_widget)
        single_layout.addWidget(
            single_size_grip, alignment=Qt.AlignRight | Qt.AlignBottom
        )
        # single_layout.addStretch()

        single_button = QPushButton("Privacy Risk Analyze")
        single_button.clicked.connect(
            lambda: self.show_inference_result(self.single_tree_widget, "Single")
        )
        single_layout.addWidget(single_button)
        self.layout.addLayout(single_layout)

        # Multiple Sink Inference
        multiple_layout = QVBoxLayout()
        multiple_label = QLabel(title_s + "Multiple-Sink Inference:")
        multiple_layout.addWidget(multiple_label)
        self.multiple_tree_widget = QTreeWidget()
        self.multiple_tree_widget.setHeaderLabels(["Groups", "Group of Chains"])

        for group_num_i, chainlist_ut in enumerate(self.multiple_chains):

            multiple_tree_item = QTreeWidgetItem(
                [f"Group {group_num_i+1}", f"Chains of Group {group_num_i+1}"]
            )

            self.multiple_tree_widget.addTopLevelItem(multiple_tree_item)

            child_tree_widget = QTreeWidget()
            child_tree_widget.setHeaderLabels(["Sinks", "Chains"])

            for sink_num_i, chainlist_u in enumerate(chainlist_ut):
                number_single_i, maxlen_single_i = (
                    chainlist_u.number,
                    chainlist_u.max_len[self.index],
                )
                child_tree_item = QTreeWidgetItem(
                    [
                        f"Sink {sink_num_i+1},Group {group_num_i+1}",
                        f"Chains of Sink {sink_num_i+1},Group {group_num_i+1}",
                    ]
                )
                child_tree_widget.addTopLevelItem(child_tree_item)

                table_widget = QTableWidget(number_single_i, maxlen_single_i)
                table_widget.setHorizontalHeaderLabels(
                    [f"App{i_i+1}" for i_i in range(maxlen_single_i)]
                )

                table_height = table_widget.horizontalHeader().height()

                for row_i, chain_u in enumerate(chainlist_u.chains):
                    appnames_l: list = chain_u.appnames[::-1]
                    for column_i in range(len(appnames_l)):
                        table_widget.setItem(
                            row_i, column_i, QTableWidgetItem(appnames_l[column_i])
                        )

                    table_height += table_widget.rowHeight(row_i)
                table_widget.setFixedHeight(table_height)
                table_item = QTreeWidgetItem(child_tree_item)
                child_tree_widget.setItemWidget(table_item, 1, table_widget)

            self.multiple_tree_widget.addTopLevelItem(multiple_tree_item)
            self.multiple_tree_widget.setItemWidget(
                multiple_tree_item, 1, child_tree_widget
            )

        multiple_layout.addWidget(self.multiple_tree_widget)
        multiple_size_grip = QSizeGrip(self.multiple_tree_widget)
        multiple_layout.addWidget(
            multiple_size_grip, alignment=Qt.AlignRight | Qt.AlignBottom
        )
        # multiple_layout.addStretch()

        multiple_button = QPushButton("Privacy Risk Analyze")
        multiple_button.clicked.connect(
            lambda: self.show_inference_result(self.multiple_tree_widget, "Multiple")
        )

        multiple_layout.addWidget(multiple_button)
        self.layout.addLayout(multiple_layout)

        self.setLayout(self.layout)
        self.setWindowTitle("Leakage Groups")
        self.show()

    def get_number_and_max_length(self, chainlist_ul):
        number_i, max_len_i = 0, 0
        for chainlist_u in chainlist_ul:
            max_len_i = max(max_len_i, chainlist_u.max_len[0])
            number_i += 1
        return number_i, max_len_i

    def show_inference_result(self, tree_widget, infer_type_s: str = "Single"):
        selected_item = tree_widget.currentItem()

        row_i = -1
        if selected_item:
            row_i = tree_widget.indexOfTopLevelItem(selected_item)
            if row_i == -1:
                parent_item = selected_item.parent()
                if parent_item:
                    row_i = tree_widget.indexOfTopLevelItem(parent_item)
        else:
            QMessageBox.warning(self, "Warning", "Please select a group first.")

        if infer_type_s == "Single":
            chainlist_u = self.single_chains[row_i]
            inferences_d: dict = self.single_inference[chainlist_u]
            chainlist_ut = (chainlist_u,)
        else:
            chainlist_ut = self.multiple_chains[row_i]
            inferences_d: dict = self.multiple_inference[chainlist_ut]

        self.details_ui = DetailsUI(
            chainlist_ut, inferences_d, row_i, infer_type_s, self.index
        )
        self.details_ui.show()


class DetailsUI(QWidget):
    def __init__(
        self,
        chainlist_ut,
        inferences_d: dict,
        row_i: int,
        infer_type_s: str,
        index_i: int,
    ):
        super().__init__()
        self.chainlists = chainlist_ut
        self.inferences = inferences_d
        self.row = row_i
        self.type = infer_type_s
        self.index = index_i

        self.layout = QVBoxLayout()

        label_s = f"Multiple-Sink Inference for Group {self.row + 1}:\n"
        if self.type == "Single":
            label_s = f"Single-Sink Inference for Chain {self.row + 1}:\n"
        title_label = QLabel(label_s)
        self.layout.addWidget(title_label)

        chaining_label = QLabel(f"Chaining Graph of Cross-App Chains:")
        self.layout.addWidget(chaining_label)

        plot_canvas = PlotCanvas(self.chainlists, self.index)
        self.layout.addWidget(plot_canvas)
        plot_size_grip = QSizeGrip(plot_canvas)
        self.layout.addWidget(plot_size_grip, alignment=Qt.AlignRight | Qt.AlignBottom)
        # self.layout.addStretch()

        # relations_label = QLabel(f"Relation(s) in Each Cross-App Chain:")
        # self.layout.addWidget(relations_label)

        results_label = QLabel(f"Privacy Threats due to Cross-App Chain:")
        self.layout.addWidget(results_label)

        result_columns_l = [
            "Involved Apps",
            "Privacy Label",
            "Sensitive State",
            "Sensitive Device",
            "Inference Probability",
            "Leak Type",
        ]
        result_widget = QTableWidget()
        result_widget.setColumnCount(len(result_columns_l))
        result_widget.setHorizontalHeaderLabels(result_columns_l)
        result_height = result_widget.horizontalHeader().height()
        for state_s, inference_u in inferences_d.items():
            if inference_u.threat is None:
                continue
            row_i = result_widget.rowCount()
            result_widget.insertRow(row_i)
            result_height += result_widget.rowHeight(row_i)

            result_widget.setItem(
                row_i, 0, QTableWidgetItem(", ".join(list(inference_u.appnames)))
            )
            result_widget.setItem(
                row_i,
                1,
                QTableWidgetItem(
                    ", ".join(
                        [
                            f"({PRIVACY_ABBREV_D[item_s]}){item_s}"
                            for item_s in inference_u.privacy
                        ]
                    )
                ),
            )
            result_widget.setItem(row_i, 2, QTableWidgetItem(inference_u.state))
            result_widget.setItem(row_i, 3, QTableWidgetItem(inference_u.device))
            result_widget.setItem(
                row_i, 4, QTableWidgetItem(str(inference_u.inference))
            )
            result_widget.setItem(row_i, 5, QTableWidgetItem(str(inference_u.threat)))

        result_widget.setFixedHeight(result_height)
        self.layout.addWidget(result_widget)

        result_size_grip = QSizeGrip(result_widget)
        self.layout.addWidget(
            result_size_grip, alignment=Qt.AlignRight | Qt.AlignBottom
        )
        result_size_grip.setFixedHeight(10)
        # self.layout.addStretch()

        self.setLayout(self.layout)
        # self.setWindowTitle(f"Group {group_number + 1} Details")


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(
        self, chainlist_l, index_i, parent=None, width=150, height=150, dpi=100
    ):
        self.chainlist = chainlist_l
        self.index = index_i

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        self.setParent(parent)
        self.graph = nx.DiGraph()
        self.plot()

    def plot(self):
        self.axes.clear()
        appnames_e: set = set()
        tca_nodes_d: dict = {}
        tca_edges_e: set = set()
        chain_edges_d: dict = {}

        for chainlist_u in self.chainlist:
            triggers_l = chainlist_u.triggers[self.index]
            conditions_l = chainlist_u.conditions[self.index]
            actions_l = chainlist_u.actions[self.index]

            for tca_l in [triggers_l, conditions_l, actions_l]:
                for tca_u in tca_l:
                    tca_nodes_d[tca_u] = tca_u.get_repr()
                    appnames_e.add(tca_u.appname)

                    rule_conn_ul = tca_u.rule_connects
                    for other_u in rule_conn_ul:
                        tcas_t: tuple = (other_u, tca_u)
                        tca_edges_e.add(tcas_t)

                    chain_conn_ul = tca_u.chain_connects
                    for connects_ut in chain_conn_ul:
                        other_u, conn_m, chain_m = connects_ut
                        tcas_t: tuple = (other_u, tca_u)
                        chain_edges_d[tcas_t] = f"{str(conn_m)}-{str(chain_m)}"

        appnames_len_i = len(appnames_e)
        default_color_l = [
            "r",
            "b",
            "g",
            "m",
            "y",
            "c",
            "gray",
            "tan",
            "orange",
            "olive",
            "lightgreen",
            "lightcyan",
            "pink",
            "violet",
        ]
        if appnames_len_i > len(default_color_l):
            add_colors_l: list = [
                "#%06x" % random.randint(0, 0xFFFFFF)
                for _ in range(appnames_len_i - len(default_color_l))
            ]
            default_color_l.extend(add_colors_l)
        appname_color_d: dict = dict(zip(list(appnames_e), default_color_l))
        color_appname_l: list = [
            mpatches.Patch(color=color_s, label="App: " + appname_s)
            for appname_s, color_s in appname_color_d.items()
        ]

        tca_nodes_l: list = list(tca_nodes_d.keys())
        self.graph.add_nodes_from(tca_nodes_l)

        tca_edges_l = list(tca_edges_e)
        self.graph.add_edges_from(tca_edges_l, length=5000)

        chain_edges_l = list(chain_edges_d.keys())

        positions_l: list = nx.spring_layout(self.graph, k=1.5)

        for tca_node_u in tca_nodes_l:
            node_shape_s = "s"
            if tca_node_u.type == TcaEnum.TRIGGER:
                node_shape_s = "o"
            elif tca_node_u.type == TcaEnum.CONDITION:
                node_shape_s = "d"

            nx.draw_networkx_nodes(
                self.graph,
                positions_l,
                nodelist=[tca_node_u],
                node_shape=node_shape_s,
                node_size=2000,
                node_color=appname_color_d[tca_node_u.appname],
                ax=self.axes,
            )

        nx.draw_networkx_labels(
            self.graph,
            positions_l,
            labels=tca_nodes_d,
            font_size=15,
            font_color="black",
            font_weight="bold",
            ax=self.axes,
        )

        nx.draw_networkx_edges(
            self.graph,
            positions_l,
            edgelist=tca_edges_l,
            arrowstyle="-|>",
            arrowsize=20,
            width=2.5,
            edge_color="gray",
            node_size=3000,
            connectionstyle="arc3,rad=0.1",
            ax=self.axes,
        )
        nx.draw_networkx_edges(
            self.graph,
            positions_l,
            edgelist=chain_edges_l,
            arrowstyle="-|>",
            arrowsize=20,
            width=5,
            edge_color="violet",
            node_size=3000,
            connectionstyle="arc3,rad=0.05",
            style=":",
            ax=self.axes,
        )
        nx.draw_networkx_edge_labels(
            self.graph,
            positions_l,
            edge_labels=chain_edges_d,
            font_size=12,
            font_color="red",
            ax=self.axes,
        )
        self.axes.legend(
            handles=color_appname_l, bbox_to_anchor=(1.05, 0), loc=3, borderaxespad=0
        )
        self.fig.text(
            0.5,
            0.05,
            "○:Trigger   ◇:Condition   □:Action   ─:Rule   ┈:Chain",
            ha="center",
            fontsize=13,
            bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5},
        )

        self.axes.legend(handles=color_appname_l)
        self.draw()


experiment_s = "original"

if len(sys.argv) > 1:
    experiment_s = sys.argv[1]

(
    applications_l,
    fat_applications_l,
    total_apps_d,
    fat_apps_d,
    empty_apps_d,
    clean_apps_d,
    used_apps_d,
    clean_apps_i,
    used_apps_i,
) = read_appinfos(FILES_EXAMPLES_PATH_S)

appnames_cases_l = CASE_STUDY_CASES_D.get(experiment_s, [])
appnames_l = list(map(CASE_STUDY_APPS_D.get, appnames_cases_l))
select_applications_l = [
    get_application_by_name(applications_l, appname_s) for appname_s in appnames_l
]

result_u = MultipleAppChainsClass(select_applications_l, fat_include_b=True)
app = QApplication(sys.argv)
mainWin = MainUI(result_u)
print_memory_usage()
sys.exit(app.exec())
