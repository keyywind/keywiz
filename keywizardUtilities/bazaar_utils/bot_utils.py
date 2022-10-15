from typing import Tuple, List 
import ctypes, numpy, cv2, os

class BotUtils:
    library_name = os.path.join(os.path.dirname(__file__), "bot_utils.dll")
    library      = ctypes.cdll.LoadLibrary(library_name)
    library.get_multiple_boundary.argtypes    = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, 
        ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t
    ]
    library.get_multiple_boundary.restype     = ctypes.c_size_t 
    library.select_items_by_name.argtypes     = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.c_size_t, ctypes.c_double 
    ]
    library.select_items_by_name.restype      = ctypes.c_size_t 
    library.get_bounding_boxes.argtypes       = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t 
    ]
    library.get_bounding_boxes.restype        = ctypes.c_size_t 
    library.select_items_by_quantity.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t 
    ]
    library.select_items_by_quantity.restype  = ctypes.c_size_t 
    @classmethod 
    def get_multiple_boundary(class_, image_list : numpy.ndarray) -> List[ Tuple[ int, int ] ]:
        if (image_list.dtype != numpy.uint8):
            image_list = numpy.uint8(image_list)
        n_img = image_list.__len__()
        ___SX = (ctypes.c_size_t * n_img)()
        ___EX = (ctypes.c_size_t * n_img)()
        n_itm = class_.library.get_multiple_boundary(___SX, ___EX, image_list.ctypes.data, n_img, * image_list.shape[1:3])
        return list(zip(___SX[:n_itm], ___EX[:n_itm]))
    @classmethod 
    def select_items_by_name(class_, names_wanted : List[ str ], names_found : List[ str ], name_thresh : float) -> List[ Tuple[ int, int ] ]:
        num_wanted       = names_wanted.__len__()
        num_found        = names_found.__len__()
        __names_wanted   = (ctypes.c_char_p * num_wanted)(*[  string.encode("UTF-8") for string in names_wanted  ])
        __names_found    = (ctypes.c_char_p * num_found) (*[  string.encode("UTF-8") for string in names_found   ])
        __indices_wanted = (ctypes.c_size_t * num_found)()
        __indices_found  = (ctypes.c_size_t * num_found)()
        num_selected     = class_.library.select_items_by_name(
            __indices_wanted, __indices_found, __names_wanted, __names_found, num_wanted, num_found, name_thresh)
        return list(zip(list(__indices_wanted)[:num_selected], list(__indices_found)[:num_selected]))
    @classmethod 
    def get_bounding_boxes(class_, image : numpy.ndarray) -> List[ Tuple[ int, int, int, int ] ]:
        if (image.dtype != numpy.uint8):
            image = numpy.uint8(image)
        __SX = (ctypes.c_size_t * 20)()
        __SY = (ctypes.c_size_t * 20)()
        __EX = (ctypes.c_size_t * 20)()
        __EY = (ctypes.c_size_t * 20)()
        numb = class_.library.get_bounding_boxes(__SX, __SY, __EX, __EY, image.ctypes.data, * image.shape[0:2])
        return list(zip(
            list(__SX)[:numb], list(__SY)[:numb],
            list(__EX)[:numb], list(__EY)[:numb]
        ))
    @classmethod 
    def select_items_by_quantity(class_, quantity_wanted : List[ int ], quantity_found : List[ int ], indices_found : List[ int ]) -> List[ int ]:
        __number_items    = len(indices_found)
        ___indices_found  = (ctypes.c_size_t * __number_items)()
        __quantity_wanted = (ctypes.c_size_t * __number_items)(*quantity_wanted)
        __quantity_found  = (ctypes.c_size_t * __number_items)(*quantity_found)
        __indices_found   = (ctypes.c_size_t * __number_items)(*indices_found)
        number_items      = class_.library.select_items_by_quantity(___indices_found, __quantity_wanted, __quantity_found, __indices_found, __number_items)
        return list(___indices_found)[:number_items]
class DigitUtils:
    model_name       = os.path.join(os.path.join(os.path.dirname(__file__), "./../../keywizardModel"), "digit_predictor.pb")
    model            = cv2.dnn.readNetFromTensorflow(model_name)
    DEFAULT_QUANTITY = 999_999_999 
    MIN_DIGIT_AREA   = 10
    MAX_DIGIT_WIDTH  = 10
    IMG_SHAPE        = (32, 32, 1)
    @classmethod 
    def _basic_predict(class_, image_list : numpy.ndarray) -> numpy.ndarray:
        predictor = class_.model 
        (h, w)    = image_list[0].shape[0:2]
        def predict_blob(blob_image : numpy.ndarray) -> numpy.ndarray:
            nonlocal predictor
            predictor.setInput(blob_image)
            return predictor.forward()
        blob_list   = [
            cv2.dnn.blobFromImage(__image, 1.0, (w, h))
                for __image in numpy.float32(image_list) / 255.0
        ]
        return numpy.stack([  predict_blob(__image) for __image in blob_list  ])
    @classmethod 
    def _images_to_integer(class_, image_list : numpy.ndarray) -> int:
        integer_list   = class_._basic_predict(image_list)
        integer_list   = [  int(numpy.argmax(integer)) for integer in integer_list  ]
        integer_string = ""
        for integer in integer_list:
            char = str(integer)
            if (char.isnumeric()):
                integer_string += char 
        return (int(integer_string) if (integer_string.__len__()) else (class_.DEFAULT_QUANTITY))
    @classmethod 
    def _image_to_digit_images(class_, image : numpy.ndarray) -> List[ numpy.ndarray ]:
        cont, c_image = cv2.connectedComponents(image)
        images        = []
        for (sx, sy, ex, ey) in BotUtils.get_bounding_boxes(c_image):
            dx = ex - sx
            dy = ey - sy
            if ((dx * dy) <= class_.MIN_DIGIT_AREA):
                continue 
            if (dx >= class_.MAX_DIGIT_WIDTH):
                dx = dx // 2
                images.append(image[ sy : ey, sx : sx + dx ])
                images.append(image[ sy : ey, sx + dx : ex ])
            else:
                images.append(image[ sy : ey, sx : ex ])
        return images 
    @classmethod 
    def _center_digit_images(class_, image_list : List[ numpy.ndarray ]) -> numpy.ndarray:
        def center_digit_image(image : numpy.ndarray) -> numpy.ndarray:
            empty_mask = numpy.zeros(shape = class_.IMG_SHAPE, dtype = numpy.uint8)
            (h, w)     = image.shape[0:2]
            (H, W)     = class_.IMG_SHAPE[0:2]
            (y, x)     = ((H - h) // 2, (W - w) // 2)
            empty_mask[ y : y + h, x : x + w ] = numpy.expand_dims(image, axis = 2) 
            return empty_mask 
        return numpy.stack([
            center_digit_image(image) for image in image_list     
        ])
    @classmethod 
    def image_to_integer(class_, image : numpy.ndarray) -> int:
        digit_images = class_._image_to_digit_images(image)
        digit_images = class_._center_digit_images(digit_images)
        return class_._images_to_integer(digit_images)
    
if (__name__ == "__main__"):
    
    n = 1
    