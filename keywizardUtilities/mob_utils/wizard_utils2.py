from typing import Callable, Tuple, Union, List
import numpy, cv2, os
class ModelManager:
    
    book_predictor  = None
    
    pass_predictor  = None
        
    deck_predictor  = None
    
    orbH_predictor  = None
    
    orbM_predictor  = None
    
    card_predictor  = None
    
    digH_predictor  = None
    
    digM_predictor  = None
    
    digi_predictor  = None
    
    STATE_IDLE      = 0
    
    STATE_COMBAT    = 1
    
    STATE_ANIMATION = 2
    
    CARD_ATTACK     = 0
    
    CARD_ENCHANT    = 1
    
    CARD_HEAL       = 2
    
    ACTION_ATTACK   = 0
    
    ACTION_HEAL     = 1
    
    ACTION_PASS     = 2
    
    """(book_state, pass_state)"""
    STATES = {
        0 : {  0 : STATE_ANIMATION, 1 : STATE_COMBAT     },
        1 : {  0 : STATE_IDLE,      1 : STATE_ANIMATION  }
    }
    
    @classmethod
    def initialize(class_, 
            book_model_name : str, pass_model_name : str, card_model_name : Union[ str, List[ str ] ],
            deck_model_name : str, orbH_model_name : str, orbM_model_name : str,
            digH_model_name : str, digM_model_name : str, digi_model_name : str) -> "ModelManager":
        
        def check_model_files() -> bool:
            model_files = [  
                book_model_name, pass_model_name, *card_model_name,
                deck_model_name, orbH_model_name, orbM_model_name,
                digH_model_name, digM_model_name, digi_model_name
            ]
            error_list  = [
                model_file for model_file in model_files 
                    if not (os.path.isfile(model_file))    
            ]
            if (error_list.__len__()):
                error_message = "The following models could not be found: \n" + "\n".join([
                    "[ {} ] \"{}\"".format(index + 1, filename)
                        for index, filename in enumerate(error_list)
                ])
                raise IOError(error_message)
            return True
        
        card_model_name = (([  card_model_name  ]) if (isinstance(card_model_name, str)) else (card_model_name))
        
        if (check_model_files()):
            (class_.book_predictor, class_.pass_predictor, class_.deck_predictor) = (
                cv2.dnn.readNetFromTensorflow(book_model_name),
                cv2.dnn.readNetFromTensorflow(pass_model_name),
                cv2.dnn.readNetFromTensorflow(deck_model_name)
            )
            class_.card_predictor = [
                cv2.dnn.readNetFromTensorflow(model_name)
                    for model_name in card_model_name
            ]
            (class_.orbH_predictor, class_.orbM_predictor) = (
                cv2.dnn.readNetFromTensorflow(orbH_model_name),
                cv2.dnn.readNetFromTensorflow(orbM_model_name)
            )
            (class_.digH_predictor, class_.digM_predictor, class_.digi_predictor) = (
                cv2.dnn.readNetFromTensorflow(digH_model_name),
                cv2.dnn.readNetFromTensorflow(digM_model_name),
                cv2.dnn.readNetFromTensorflow(digi_model_name)
            )
        return class_ 
    
    @classmethod
    def basic_predict(class_, input_images : Union[ List[ numpy.ndarray ], numpy.ndarray ]       , 
                            predictor_name : Union[                                  str ]       ,
                            predictor_val  : Union[                     type(None), int  ] = None
                            ) -> "ModelManager":
        
        model_predictor = getattr(class_, predictor_name)
        
        if (predictor_val is not None):
            model_predictor = model_predictor[  predictor_val  ]
            
        (height, width) = input_images[0].shape[0:2]
        
        def predict_blob(blob_image : numpy.ndarray) -> numpy.ndarray:
            nonlocal model_predictor
            model_predictor.setInput(blob_image)
            return model_predictor.forward()
        
        blob_list       = [
            cv2.dnn.blobFromImage(__image, 1.0, (width, height))
                for __image in numpy.float32(input_images) / 255.0
        ]
        
        return numpy.stack([
            predict_blob(__image)
                for __image in blob_list
        ])
    
    @classmethod
    def determine_state(class_, book_image : numpy.ndarray, pass_image : numpy.ndarray) -> int:
        book_state = (class_.basic_predict([  book_image  ], "book_predictor")[0][0][0] >= 0.5)
        pass_state = (class_.basic_predict([  pass_image  ], "pass_predictor")[0][0][0] >= 0.5)
        return class_.STATES[  book_state  ][  pass_state  ]
    
    @classmethod
    def count_cards(class_, deck_image : numpy.ndarray) -> int:
        quantity_prediction = int(numpy.argmax(
            class_.basic_predict([  deck_image  ], "deck_predictor")[0][0]
        ))
        return quantity_prediction
    
    @classmethod
    def classify_cards(class_, card_images : Union[ List[ numpy.ndarray ], numpy.ndarray ], predictor : Union[ type(None), int ] = None) -> Tuple[ int ]:
        
        def format_indices(indices : numpy.ndarray) -> numpy.ndarray:
            return numpy.stack([
                index[0] for index in indices    
            ])
        
        def find_indices(indices : numpy.ndarray, value : int) -> numpy.ndarray:
            return numpy.where(indices == value)[0]
        
        cards_classified = format_indices(
            numpy.argmax(class_.basic_predict(card_images, "card_predictor", predictor_val = predictor), axis = 2)
        )
        
        cards_classified = (attack_spells, enchant_spells, healing_spells) = (
            find_indices(cards_classified, value = 0),
            find_indices(cards_classified, value = 1),
            find_indices(cards_classified, value = 2)
        )
        
        return cards_classified
    
    @classmethod 
    def find_card_combination(class_, card_images : Union[  List[ numpy.ndarray ], numpy.ndarray  ]       , 
                                      should_heal : Union[               Callable, type(None)     ] = None,
                                      predictor   : Union[                       type(None), int  ] = None,  
                                      ) -> Tuple[  Tuple[ Union[ int, type(None) ] ], Tuple[ int ], int  ]:
        
        (attack_spells, enchant_spells, healing_spells) = class_.classify_cards(card_images, predictor)
        
        if ((healing_spells.__len__()) and (should_heal is not None) and (should_heal())):
            
            cards = (
                int(numpy.random.choice(healing_spells)),
                None
            )
            
            card_types  = (class_.CARD_HEAL, None)
            
            action_type = (class_.ACTION_HEAL)
            
        elif ((attack_spells.__len__()) and (enchant_spells.__len__())):
            
            cards = (
                int(numpy.random.choice(enchant_spells)),
                int(numpy.random.choice(attack_spells))
            )
            
            card_types = (class_.CARD_ENCHANT, class_.CARD_ATTACK)
            
            action_type = (class_.ACTION_ATTACK)
            
        elif (attack_spells.__len__()):
            
            cards = (
                int(numpy.random.choice(attack_spells)),
                None
            )
            
            card_types = (class_.CARD_ATTACK, None)
            
            action_type = (class_.ACTION_ATTACK)
            
        else:
            
            cards = (
                None,
                None
            )
            
            card_types = (None, None)
            
            action_type = (class_.ACTION_PASS)
            
        return (cards, card_types, action_type)
        
    @classmethod
    def detect_health_mana_scores(class_, orbs_image : numpy.ndarray) -> Tuple[ int ]:
        
        prediction_result = (health_prediction, mana_prediction) = (
            int(numpy.argmax(class_.basic_predict([  orbs_image  ], "orbH_predictor")[0][0])),
            int(numpy.argmax(class_.basic_predict([  orbs_image  ], "orbM_predictor")[0][0]))
        )
        
        return prediction_result
    
    @classmethod
    def determine_health_digit_count(class_, health_digit_image : numpy.ndarray) -> int:
        
        quantity_prediction = int(numpy.argmax(
            class_.basic_predict([  health_digit_image  ], "digH_predictor")[0][0]
        )) 
        return quantity_prediction + 1
    
    @classmethod
    def determine_mana_digit_count(class_, mana_digit_image : numpy.ndarray) -> int:
        
        quantity_prediction = int(numpy.argmax(
            class_.basic_predict([  mana_digit_image  ], "digM_predictor")[0][0]
        )) 
        return quantity_prediction + 1
    
    @classmethod 
    def classify_digits(class_, digit_image_list : Tuple[ numpy.ndarray, List[ numpy.ndarray ] ], combine_digits : bool = False) -> Tuple[ int, List[ int ] ]:
        
        prediction_results = class_.basic_predict(digit_image_list, "digi_predictor")
        
        prediction_results = [  int(numpy.argmax(prediction_result[0])) for prediction_result in prediction_results  ]
        
        if (combine_digits):
            
            return int("".join(f"{digit}" for digit in prediction_results))
        
        return prediction_results
        
if (__name__ == "__main__"):
    
    book_model_name = "./wizard_models/book_model.pb"
    
    pass_model_name = "./wizard_models/pass_model.pb"
    
    card_model_name = [  "./wizard_models/meteor/card_model.pb", "./wizard_models/tempest/card_model.pb"  ]
    
    deck_model_name = "./wizard_models/deck_model.pb"
    
    orbH_model_name = "./wizard_models/orbH_model.pb"
    
    orbM_model_name = "./wizard_models/orbM_model.pb"
    
    digH_model_name = "./wizard_models/digH_model.pb"
    
    digM_model_name = "./wizard_models/digM_model.pb"
    
    digi_model_name = "./wizard_models/digi_model.pb"
    
    ModelManager.initialize(
        book_model_name, pass_model_name, card_model_name,
        deck_model_name, orbH_model_name, orbM_model_name,
        digH_model_name, digM_model_name, digi_model_name
    )
    
    test = 2
    
    if (test == 1):
        
        test_image = "./orb_trainer/numbers_13x18/4.png"
        
        test_image = cv2.imread(test_image)
        
        prediction_result = ModelManager.classify_digits([test_image])
        
        print(prediction_result)
        
    elif (test == 2):
        
        test_images = [
            "./orb_trainer/numbers_13x18/6.png",    
            "./orb_trainer/numbers_13x18/0.png",   
            "./orb_trainer/numbers_13x18/8.png" 
        ]
        
        test_images = [
            cv2.imread(image_name) for image_name in test_images    
        ]
        
        prediction_result = ModelManager.classify_digits(test_images, combine_digits = True)
        
        print(prediction_result)