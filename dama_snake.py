import random
import maya.cmds as cmds
import pymel.core as pmc
from collections import namedtuple
import maya.api.OpenMaya as om2
import maya.api.OpenMayaUI as om2ui
import maya.api.OpenMayaRender as om2r
from PySide2 import QtWidgets, QtCore

##################################################
#---------------Global Variables------------------
##################################################

K_CMD_NAME = "dama_snake"
K_NODE_NAME = "dama_snake"
K_TYPE_ID = om2.MTypeId(0x0012eeff)
K_DRAW_DB = "drawdb/geometry/dama_snake"
K_DRAW_ID = "Dama_Snake"
K_OVERRIDE_NAME = "dama_snake_override"

##################################################
#----------------Snake Stage----------------------
##################################################


class Snake_Square(object):
    """
    Generate namedtuple object, to cut the scence as grid.
    """

    def __init__(self, tuple_name, square_size):
        current_index = 0
        if square_size == 0:
            x_pos = [0]
            y_pos = [0]
            square_size = (0, 0)
        else:
            x_pos = range(800)[::square_size]
            y_pos = range(600)[::square_size]
            square_size = (square_size, square_size)

        self._square = []
        for x in x_pos:
            for y in y_pos:
                square_tuple = tuple_name(current_index, om2.MPoint(x, y),
                                          square_size)
                self._square.append(square_tuple)
                current_index += 1

    def __len__(self):
        return len(self._square)

    def __getitem__(self, position):
        return self._square[position]


class Dama_Snake_Window(QtWidgets.QWidget):
    """
    Create Qt Widget. Tear off and look through camera we created in Dama_Snake_Cmd.
    """

    def __init__(self):
        super(Dama_Snake_Window, self).__init__()
        # - Generate square info.
        global SNAKE_DATA
        self.snake_data = SNAKE_DATA
        self.square_tuple = namedtuple('square', ['index', 'position', 'size'])
        self.square_size = 10
        self.snake_data.scence_square = Snake_Square(self.square_tuple,
                                                     self.square_size)

        self.clean_stage()
        self.snake_window()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.scence_refresh)

    # - Window Setting.
    def snake_window(self):
        self.setWindowTitle('Dama Snake')
        self.setFixedSize(822, 622)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        cmds.setParent('MayaWindow')
        model_editor = cmds.modelEditor(camera=self.snake_data.camera_name)
        self.qt_ctrl = pmc.windows.toQtControl(model_editor)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.qt_ctrl)

    def space_key_statue(self):
        # - First press space key.
        if not self.run_status:
            self.run_status = 1
            self.snake_generation()
            self.food_generation()
        # - Start or Pause game.
        if self.pause_status:
            self.pause_status = 0
            self.snake_speed = 200 - int(
                (len(self.snake_data.snake_square) - 3)) * 0.0415
            self.timer.start(self.snake_speed)
        else:
            self.pause_status = 1
            self.timer.stop()

    # - Keyboard press event
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            if self.snake_direction != (1, 0) and self.key_lock == 0:
                self.snake_direction = (-1, 0)
        if event.key() == QtCore.Qt.Key_Right:
            if self.snake_direction != (-1, 0) and self.key_lock == 0:
                self.snake_direction = (1, 0)
        if event.key() == QtCore.Qt.Key_Up:
            if self.snake_direction != (0, -1) and self.key_lock == 0:
                self.snake_direction = (0, 1)
        if event.key() == QtCore.Qt.Key_Down:
            if self.snake_direction != (0, 1) and self.key_lock == 0:
                self.snake_direction = (0, -1)
        if event.key() == QtCore.Qt.Key_Space:
            self.space_key_statue()
        if event.key() == QtCore.Qt.Key_Escape:
            self.game_over()
        self.key_lock = 1

    def snake_generation(self):
        snake_square = [
            self.snake_data.scence_square[2489],
            self.snake_data.scence_square[2429],
            self.snake_data.scence_square[2369]
        ]
        self.snake_data.snake_square = snake_square

    def food_generation(self):
        scence_square = [i for i in self.snake_data.scence_square]
        for i in self.snake_data.snake_square:
            scence_square.remove(i)
        food_square = random.choice(self.snake_data.scence_square)
        self.snake_data.food = food_square

    def get_move_offset(self):
        direction = self.snake_direction

        if direction[0] == 1:
            return 60
        elif direction[0] == -1:
            return -60
        elif direction[1] == 1:
            return 1
        elif direction[1] == -1:
            return -1

    def scence_refresh(self):
        scence_square = self.snake_data.scence_square
        snake_square = self.snake_data.snake_square
        move_offset = self.get_move_offset()
        snake_head = snake_square[0]
        new_index = snake_head.index + move_offset
        head_vrange = [i for i in self.scence_vrange
                       if snake_head.index in i][0]

        if not new_index in range(len(scence_square)):
            self.game_over()
        elif self.snake_direction[1] != 0 and not new_index in head_vrange:
            self.game_over()
        elif len(snake_square) == len(scence_square) - 1:
            self.game_over(win=1)
        else:
            # - Update snake head position.
            new_head = scence_square[new_index]
            self.key_lock = 0
            snake_square.insert(0, new_head)
            # - Update snake tail position.
            if new_head == self.snake_data.food:
                self.food_generation()
            else:
                tail = snake_square.pop()

            snake_body = snake_square[1:]
            if new_head in snake_body:
                self.game_over()
            else:
                self.score = len(snake_square) - 3
                self.snake_speed = 200 - int(
                    (len(self.snake_data.snake_square) - 3)) * 0.0415
                self.timer.start(self.snake_speed)

                cmds.refresh()

    # - Initialization Variables
    def clean_stage(self):
        self.snake_data.food = Snake_Square(self.square_tuple, 0)[0]
        self.snake_data.snake_square = [Snake_Square(self.square_tuple, 0)[0]]
        self.snake_data.snake_color = om2.MColor((0.0, 0.0, 0.0, 1.0))
        self.snake_data.food_color = om2.MColor((1.0, 1.0, 1.0, 1.0))
        self.pause_status = 1
        self.run_status = 0
        self.snake_speed = 200
        self.key_lock = 0
        self.snake_direction = (1, 0)
        self.score = 0
        scence_vrange = [i for i in range(4800)]
        self.scence_vrange = [
            scence_vrange[i:i + 60] for i in range(0, 4800, 60)
        ]

    def game_over(self, win=0):
        self.timer.stop()
        if win == 0:
            pop_msg = "Game Over!\nScore: {}".format(self.score)
        else:
            pop_msg = "You Win!\nScore: {}".format(self.score)

        QtWidgets.QMessageBox.warning(self, pop_msg, pop_msg,
                                      QtWidgets.QMessageBox.Ok)
        self.clean_stage()
        cmds.refresh()

    def closeEvent(self, event):
        self.timer.stop()


##################################################
#-------------Custom Maya Command---------------
##################################################


class Dama_Snake_Cmd(om2.MPxCommand):
    """
    Create Maya Command.
    """

    def __init__(self):
        super(Dama_Snake_Cmd, self).__init__()
        global SNAKE_DATA
        self.snake_data = SNAKE_DATA

    def doIt(self, *args):

        self.snake_data.snake_camera = pmc.camera(
            n='Snake_Camera', p=[28.0, 21.0, 28.0], rot=[-27.938, 45.0, 0])[0]
        self.snake_data.snake_camera.visibility.set(0)
        self.snake_data.camera_name = self.snake_data.snake_camera.name()

        self.snake_data.snake_win = Dama_Snake_Window()

        self.snake_data.snake_win.show()
        self.snake_data.node_list = cmds.createNode("dama_snake")
        cmds.select(cl=1)
        print("Let's play it!")


class Dama_Snake_Data(om2.MUserData):
    """
    Save Game Temp Data.
    """

    def __init__(self):
        # - False: Do not delete after draw.
        super(Dama_Snake_Data, self).__init__(False)


SNAKE_DATA = Dama_Snake_Data()

##################################################
#-------------Dama Snake Node---------------------
##################################################


class Dama_Snake(om2ui.MPxLocatorNode):
    """
    This is Dama Snake Node class.
    """

    def __init__(self):
        super(Dama_Snake, self).__init__()

    @classmethod
    def initialize(cls):
        return

    def excludeAsLocator(self):
        """
        When the modelPanel is set to not draw locators, the custom locator will also be drawn.
        """
        return False


class Dama_Snake_Override(om2r.MPxDrawOverride):
    """
    Override node in viewport2.0
    """

    def __init__(self, obj):
        super(Dama_Snake_Override, self).__init__(obj,
                                                  Dama_Snake_Override.draw)
        global SNAKE_DATA
        self.snake_data = SNAKE_DATA

    def isBounded(self, obj_path, camera_path):
        return False

    def boundingBox(self, obj_path, camera_path):
        return om2.MBoundingBox()

    def supportedDrawAPIs(self):
        return (om2r.MRenderer.kAllDevices)

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        data = old_data
        if not isinstance(data, Dama_Snake_Data):
            data = self.snake_data

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, obj_path, draw_manager, frame_context, data):
        if not isinstance(data, Dama_Snake_Data):
            return

        camera_path = frame_context.getCurrentCameraPath()

        if data.camera_name and self.camera_exists(
                data.camera_name) and not self.is_camera_match(
                    camera_path, data.camera_name):
            return

        draw_manager.beginDrawable()
        self.draw_snake(draw_manager, data)
        self.draw_food(draw_manager, data)

        draw_manager.endDrawable()

    def draw_food(self, draw_manager, data):
        square_pos = data.food.position
        square_size = data.food.size
        square_color = data.food_color
        self.draw_square(draw_manager, square_pos, square_size, square_color)

    def draw_snake(self, draw_manager, data):
        snake_square = data.snake_square
        for i in snake_square:
            square_pos = i.position
            square_size = i.size
            square_color = data.snake_color
            self.draw_square(draw_manager, square_pos, square_size,
                             square_color)

    def draw_square(self, draw_manager, position, square_size, color):
        draw_manager.text2d(
            position,
            " ",
            alignment=om2r.MUIDrawManager.kLeft,
            backgroundSize=square_size,
            backgroundColor=color)

    def camera_exists(self, name):
        return name in cmds.listCameras()

    def is_camera_match(self, camera_path, name):
        path_name = camera_path.fullPathName()
        split_path_name = path_name.split('|')
        if len(split_path_name) >= 1:
            if split_path_name[-1] == name:
                return True
        if len(split_path_name) >= 2:
            if split_path_name[-2] == name:
                return True
        return False

    @staticmethod
    def creator(obj):
        return Dama_Snake_Override(obj)

    @staticmethod
    def draw(context, data):
        return


##################################################
#---------------Initialization--------------------
##################################################


def cmd_creator():
    """
    om2.MPxCommand.creator
    """
    return Dama_Snake_Cmd()


def node_creator():
    """
    om2.MPxLocatorNode.creator
    """
    return Dama_Snake()


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(obj):
    plugin_func = om2.MFnPlugin(obj, "400dama", "0.0.1", "test")
    # - Register node. Dependency Nodes: dama_snake.
    try:
        plugin_func.registerNode(K_NODE_NAME, K_TYPE_ID, node_creator,
                                 Dama_Snake.initialize,
                                 om2.MPxNode.kLocatorNode, K_DRAW_DB)
    except:
        om2.MGlobal.displayError(
            "Failed to register node: {0}".format(K_NODE_NAME))
        raise

    # - Register node viewport2.0 override.
    try:
        om2r.MDrawRegistry.registerDrawOverrideCreator(
            K_DRAW_DB, K_DRAW_ID, Dama_Snake_Override.creator)
    except:
        om2.MGlobal.displayError(
            "Failed to register draw override: {0}".format(K_OVERRIDE_NAME))
        raise

    # - Register command. Commands: cmds.dama_snake()self.
    try:
        plugin_func.registerCommand(K_CMD_NAME, cmd_creator)
    except:
        om2.MGlobal.displayError(
            "Failed to register Command: {0}".format(K_CMD_NAME))
        raise


def uninitializePlugin(obj):
    """
    """
    plugin_func = om2.MFnPlugin(obj)

    # - Unregister node viewport2.0 override
    try:
        om2r.MDrawRegistry.deregisterDrawOverrideCreator(K_DRAW_DB, K_DRAW_ID)
    except:
        om2.MGlobal.displayError(
            "Failed to deregister draw override: {0}".format(K_OVERRIDE_NAME))

    # - Unregister node. Dependency Nodes: dama_snake
    try:
        plugin_func.deregisterNode(K_TYPE_ID)
    except:
        om2.MGlobal.displayError(
            "Failed to unregister node: {0}".format(K_NODE_NAME))
        raise

    # - Unregister command. Commands: cmds.dama_snake()
    try:
        plugin_func.deregisterCommand(K_CMD_NAME)
    except:
        om2.MGlobal.displayError(
            "Failed to unregister command: {0}".format(K_CMD_NAME))
        raise
