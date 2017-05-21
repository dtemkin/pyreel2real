from sklearn import metrics


class Metrics(object):

    def __init__(self, actual_y, **kwargs):
        self.y1 = actual_y

    def accuracy_score(self, predicted_y, **kwargs):
        score = metrics.accuracy_score(self.y1, predicted_y, normalize=kwargs.get("normalize", True),
                                       sample_weight=kwargs.get("sample_wt", None))

        return [("score", float(score))]

    def jaccard_similarity_score(self, predicted_y, **kwargs):
        score = metrics.jaccard_similarity_score(self.y1, predicted_y, normalize=kwargs.get("normalize", True),
                                                 sample_weight=kwargs.get("sample_wt", None))

        return [("score", float(score))]

    def accuracy_recall_curve(self, pred_probs, **kwargs):
        precision, recall, thresholds = metrics.precision_recall_curve(self.y1, pred_probs, pos_label=kwargs.get("pos_label", None),
                                                                       sample_weight=kwargs.get("sample_wt", None))
        return [("precision", precision),
                ("recall", recall),
                ("thresholds", thresholds)]

    def average_accuracy(self, score_y, **kwargs):
        avg = metrics.average_precision_score(self.y1, score_y, average=kwargs.get("average", "macro"),
                                              sample_weight=kwargs.get("sample_wt", None))

        return [("average_precision", float(avg))]

    def roc_auc_score(self, score_y, **kwargs):
        auc = metrics.roc_auc_score(self.y1, score_y,
                                    average=kwargs.get("average", "macro"),
                                    sample_weight=kwargs.get("sample_wt", None))

        return [("auc", float(auc))]


    def roc_curve(self, score_y, **kwargs):
        fpr, tpr, thresholds = metrics.roc_curve(self.y1, score_y, pos_label=kwargs.get('pos_label', None),
                                                 sample_weight=kwargs.get("sample_wt", None),
                                                 drop_intermediate=kwargs.get('drop_intermediate', True))
        return [("false_pos_rate", fpr),
                ("true_pos_rate", tpr),
                ("thresholds", thresholds)]

    def cls_report(self, predicted_y, target_classes, **kwargs):
        report = metrics.classification_report(self.y1, predicted_y, target_names=target_classes,
                                               sample_weight=kwargs.get("sample_wt", None),
                                               digits=kwargs.get("digits", 2))

        return [("report", str(report))]

    def area_under_curve(self, xcoords, ycoords, **kwargs):
        auc = metrics.auc(x=xcoords, y=ycoords, reorder=kwargs.get("reorder", False))

        return [("auc", float(auc))]
