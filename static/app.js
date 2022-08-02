
new Vue({
    el:'#card',
    delimiters: ["${","}"],
    data:{
        msg:"this is my custom message",
        cardone:"start",
        flipped:false
    },
    methods: {
        toggleCard:function(card){
          card.flipped = !card.flipped;
        },
    },
});

