import os
import tensorflow as tf

PATH_TO_FROZEN_GRAPH = "\\tensorflow-models\\pretrained_model\\faster_rcnn_resnet101_coco_2018_01_28_200000\\frozen_inference_graph.pb"
 
detection_graph = tf.Graph()
with detection_graph.as_default():
 
    od_graph_def = tf.GraphDef()
 
    with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as f:
 
        serialized_graph = f.read()
        od_graph_def.ParseFromString(serialized_graph)
 
        tf.import_graph_def(od_graph_def, name = "")
#print('\n계산 그래프 로드 완료...\n')
 

import cv2
import numpy as np
 
def run_inference_for_single_image(image, graph):
    with tf.Session(graph = graph) as sess:
 
        input_tensor = graph.get_tensor_by_name('image_tensor:0')
        target_operation_names = ['num_detections', 'detection_boxes', 'detection_scores', 'detection_classes', 'detection_masks']
        tensor_dict = {}

        for key in target_operation_names:
            op = None
            try:
                op = graph.get_operation_by_name(key)
                
            except:
                continue
 
            tensor = graph.get_tensor_by_name(op.outputs[0].name)
            tensor_dict[key] = tensor
 
        if 'detection_masks' in tensor_dict:
            detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
 
        output_dict = sess.run(tensor_dict, feed_dict = {input_tensor : [image]})
            
        output_dict['num_detections'] = int(output_dict['num_detections'][0])
        output_dict['detection_classes'] = output_dict['detection_classes'][0].astype(np.uint8)
        output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
        output_dict['detection_scores'] = output_dict['detection_scores'][0]
 
        return output_dict


def draw_bounding_boxes(img, output_dict, class_info):
 
    height, width, _ = img.shape
 
    obj_index = output_dict['detection_scores'] > 0.5
    
    scores = output_dict['detection_scores'][obj_index]
    boxes = output_dict['detection_boxes'][obj_index]
    classes = output_dict['detection_classes'][obj_index]
 
    for box, cls, score in zip(boxes, classes, scores):
        # draw bounding box
        img = cv2.rectangle(img,
                            (int(box[1] * width), int(box[0] * height)),
                            (int(box[3] * width), int(box[2] * height)), class_info[cls][1], 8)
 
        # put class name & percentage
        object_info = class_info[cls][0] + ': ' + str(int(score * 100)) + '%'
        text_size, _ = cv2.getTextSize(text = object_info,
                                       fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                                       fontScale = 0.9, thickness = 2)
        img = cv2.rectangle(img,
                            (int(box[1] * width), int(box[0] * height) - 25),
                            (int(box[1] * width) + text_size[0], int(box[0] * height)),
                            class_info[cls][1], -1)
        img = cv2.putText(img,
                          object_info,
                          (int(box[1] * width), int(box[0] * height)),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        
    return img


def return_position(img, output_dict, class_info, search):
                 
    height, width, _ = img.shape
    obj_index = output_dict['detection_scores'] > 0.5
    scores = output_dict['detection_scores'][obj_index]
    boxes = output_dict['detection_boxes'][obj_index]
    classes = output_dict['detection_classes'][obj_index]

    percentage = 0.4
    position = "위치를 찾지 못했습니다"
                    
    x_1 = width / 3
    x_2 = (width / 3) * 2
    y_1 = height / 3
    y_2 = (height / 3) * 2

    for box, cls, score in zip(boxes, classes, scores):

        if class_info[cls][0] == 'toreta': 
            if score > percentage:

                x = (int(box[1] * width) + int(box[3] * width)) / 2
                y = (int(box[0] * height) + int(box[2] * height)) / 2

                print("%s %s" % (x,y))

                if x < x_1:
                    if y < y_1:
                        position = "왼쪽 위에 있어요"
                        percentage = score
                    elif y >= y_1 and y <= y_2:
                        position = "정면 왼쪽에 있어요"
                        percentage = score
                    elif y > y_2:
                        position = "왼쪽 아래에 있어요"
                        percentage = score
                elif x >= x_1 and x <= x_2:
                    if y < y_1:
                        position = "정면 위에 있어요"
                        percentage = score
                    elif y >= y_1 and y <= y_2:
                        position = "정면에 있어요"
                        percentage = score
                    elif y > y_2:
                        position = "정면 아래에 있어요"
                        percentage = score
                elif x > x_2:
                    if y < y_1:
                        position = "오른쪽 위에 있어요"
                        percentage = score
                    elif y >= y_1 and y <= y_2:
                        position = "정면 오른쪽에 있어요"
                        percentage = score
                    elif y > y_2:
                        position = "오른쪽 아래에 있어요"
                        percentage = score

    return position

           
PATH_TO_TEST_IMAGE = 'test_images'
n_images = len(os.listdir(PATH_TO_TEST_IMAGE))
TEST_IMAGE_PATHS = [os.path.join(PATH_TO_TEST_IMAGE, 'test_{}.jpg' .format(i)) for i in range(n_images)]
print('분석 대상 이미지 경로 지정 완료...')
 
class_info = {}
f = open('class_info_2.txt', 'r')
for line in f:
    info = line.split(', ')
 
    class_index = int(info[0])
    class_name = info[1]
    color = (int(info[2][1:]), int(info[3]), int(info[4].strip()[:-1]))    
    
    class_info[class_index] = [class_name, color]
f.close()
 
 
for image_path in TEST_IMAGE_PATHS:    
    img = cv2.imread(image_path)
    
    output_dict = run_inference_for_single_image(img, detection_graph)

    result = return_position(img, output_dict, class_info, 'toreta')

    print(result)
    
    result = draw_bounding_boxes(img, output_dict, class_info)
 
    test = cv2.resize(result, (360, 370))
    cv2.imshow(os.path.basename(image_path), test)
    cv2.waitKey(0)
    