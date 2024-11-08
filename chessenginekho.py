import chess as ch
import random as rd

class Engine:

    def __init__(self, board, maxDepth, color):
        self.board=board
        self.color=color
        self.maxDepth=maxDepth
    
    def getBestMove(self):
        return self.engine(None, 1)

    def evalFunct(self):
        compt = 0
        #Sums up the material values
        for i in range(64):
            compt+=self.squareResPoints(ch.SQUARES[i])
        compt += self.mateOpportunity() + self.openning() + 0.001*rd.random()
        return compt

    def mateOpportunity(self):
        if (self.board.legal_moves.count()==0):
            if (self.board.turn == self.color):
                return -999
            else:
                return 999
        else:
            return 0

    #to make the engine developp in the first moves
    def openning(self):
        if (self.board.fullmove_number<10):
            if (self.board.turn == self.color):
                return 1/30 * self.board.legal_moves.count()
            else:
                return -1/30 * self.board.legal_moves.count()
        else:
            return 0

    #مربع را به عنوان ورودی می گیرد
    #هانس برلینر مربوطه را برگردانید
    #هانس بلیمر رو سرچ کنید
    def squareResPoints(self, square):
        pieceValue = 0
        if(self.board.piece_type_at(square) == ch.PAWN):
            pieceValue = 1
        elif (self.board.piece_type_at(square) == ch.ROOK):
            pieceValue = 5.1
        elif (self.board.piece_type_at(square) == ch.BISHOP):
            pieceValue = 3.33
        elif (self.board.piece_type_at(square) == ch.KNIGHT):
            pieceValue = 3.2
        elif (self.board.piece_type_at(square) == ch.QUEEN):
            pieceValue = 8.8

        if (self.board.color_at(square)!=self.color):
            return -pieceValue
        else:
            return pieceValue

        
    def engine(self, candidate, depth):
        
        #reached max depth of search or no possible moves
        if ( depth == self.maxDepth
        or self.board.legal_moves.count() == 0):
            return self.evalFunct()
        
        else:
            #(اینو خودم نوشتم)میخوایم یک لیست از حرکت های قانونی درست کنیم.
            #legalmoves یک تابع از خود کتابخانه chess هست که حرکت های ممکن رو شناسایی میکنه.
            moveListe = list(self.board.legal_moves)
            
            #initialise newCandidate
            newCandidate = None
            #(uneven depth means engine's turn)
            if(depth % 2 != 0):
                newCandidate = float("-inf")
            else:
                newCandidate = float("inf")
            
            #analyse board after deeper moves
            for i in moveListe:

                #حرکت مهره i
                self.board.push(i)

                #ارزش مهره i
                value = self.engine(newCandidate, depth + 1) 

                #یک الگوریتم اولیه
                #نوبت engine
                if(value > newCandidate and depth % 2 != 0):
                    if (depth == 1):
                        move=i
                    newCandidate = value
                #نوبت کاربر
                elif(value < newCandidate and depth % 2 == 0):
                    newCandidate = value

                #برش آلفا بتا هرس
                #اگر حرکت قبلی با engine بود
                if (candidate != None
                 and value < candidate
                 and depth % 2 == 0):
                    self.board.pop()
                    break
                #اگر حرکت قبلی با کابر بود)
                elif (candidate != None 
                and value > candidate 
                and depth % 2 != 0):
                    self.board.pop()
                    break
                
                #لغو حرکت آخر
                self.board.pop()

            if (depth>1):
                #مقدار گره در درخت را برمی گرداند?
                return newCandidate
            else:
                #return the move (only on first move)
                return move



  



            
            


        


        



            






        
        




        




    
    