$(document).ready(function() {
   if($(this).val() != 'top')
   {
      $("#time").prop("disabled",true);
   }
   else
   {
      $("#time").prop("disabled",false);
   }


   $("#subreddit-input").keypress(function(e)
   {
      if(e.which == 13)
      {
         var subreddit = $("#subreddit-input").val();
         $("#subreddits").append("<div class='subreddit'>" + subreddit + "</div>");
         $("#subreddit-input").val("");
      }
   });

   $("#sort").change(function()
   {
	   if($(this).val() != 'top')
	   {
         $("#time").prop("disabled",true);
	   }
	   else
	   {
         $("#time").prop("disabled",false);
	   }
   });

   $("#refresh-button").click(refresh);

   $("#loadmore-button").click(loadMore);

   $("#favorites-button").click(loadFavorites);

   refresh();
});

$(document).on('click','.subreddit',function()
{
   $(this).fadeOut("fast", function() { this.remove(); });
});

var lastRequst = "";
var last_id = "";

function refresh()
{
   $("#main_div").html("");

	lastRequest = buildRequest();
   $("#loadmore-button").removeClass("loadmore");
   $("#loadmore-button").addClass("loadmore-disabled");

   $.get(lastRequest,function(data)
   {
      parse_results(data);
      $("#loadmore-button").removeClass("loadmore-disabled");
      $("#loadmore-button").addClass("loadmore");
   });
}

function loadMore()
{
	$("#loadmore-button").removeClass("loadmore");
   $("#loadmore-button").addClass("loadmore-disabled");

	request = lastRequest + "&after="+last_id;

	$.get(request,function(data)
   {
      parse_results(data);
      $("#loadmore-button").removeClass("loadmore-disabled");
      $("#loadmore-button").addClass("loadmore");
   });
}

function loadFavorites()
{
	$("#loadmore-button").removeClass("loadmore");
   $("#loadmore-button").addClass("loadmore-disabled");
   $("#main_div").html("");

   request = "/favorites";

	$.get(request,function(data)
   {
      parse_results(data);
      $("#loadmore-button").removeClass("loadmore-disabled");
      $("#loadmore-button").addClass("loadmore");
   });
}

function buildRequest()
{
   var request = "results?"

   var subreddits = [];

   $("#subreddits").children().each(function(index)
   {
      subreddits.push($(this).text());
   });

	for(var i = 0; i < subreddits.length; i++)
	{
	   request += "sub=" + subreddits[i] + "&";
	}

	var sortElement = document.getElementById('sort')
	var sortType = sortElement.options[sortElement.selectedIndex].value;
	request += "sort=" + sortType + "&";

	if(sortType == "top")
	{
		var timeElement = document.getElementById('time')
		request += "time=" + timeElement.options[timeElement.selectedIndex].value;
	}

	if(request.slice(-1) == '&')
	{
		request = request.substring(0, request.length - 1)
	}

	return request;
}

function parse_results(response_text)
{
	var results = JSON.parse(response_text);

	if(results['success'])
	{
		var images = results["data"]["images"];

		for(var i = 0; i < images.length; i++)
		{
			image_html = "<div class='Image'>";
			image_html += "<a href='http://www.reddit.com" + images[i]["reddit_link"] + "' target='_blank' class='Reddit'>";
			image_html += "<img class='Reddit' src='/images/reddit_button.gif' width='12' height='12'/></a>";

			if(images[i]["username"] != "")
			{
				var fav = "False";
				var fav_image = "/images/empty_heart.gif";
				if(images[i]["favorite"])
				{
					fav = "True"
					fav_image = "/images/heart.gif";
				}

				image_html += "<input class='Favorite' favorite='" + fav + "' type='image' id='" + images[i]["name"] + "_button' ";
				image_html += "value='" + images[i]["name"] + "' onClick='favorite(this);' src='" + fav_image + "' ";
				image_html += "width='12' height='12'/>";
			}


			image_html += "<a href='" + images[i]["image_link"] + "' target='_blank'>";
			image_html += "<img id='" + images[i]["name"] + "' src='" + images[i]["thumbnail"] + "'/></a>";
			image_html += "</div>";


			document.getElementById("main_div").innerHTML += image_html;
		}

      last_id = images[images.length - 1]["name"];
	}
	else
	{
		alert("Error!");
	}

}

function favorite(button)
{
	var request = '/favorite?wall_id=' + button.value;

	if(button.getAttribute("favorite") == 'False')
	{
		request += '&action=add';
	}
	else
	{
		request += '&action=remove';
	}

   $.get(request,function(data)
   {
      result = data.split(' ');
		var $button_element = $('#' + result[1] + '_button');

		if(result[0] == 'add')
		{
         $button_element.attr("favorite","True");
         $button_element.attr("src","/images/heart.gif");
		}
		else
		{
			$button_element.attr("favorite","False");
         $button_element.attr("src","/images/empty_heart.gif");
		}
   });
}
